package containers

import (
	"fmt"

	"github.com/fsouza/go-dockerclient"
)

type DockerRuntime struct {
	client  *docker.Client
	stopped map[string]map[ContainerID]ContainerName
}

func isRelated(volume string, container *docker.Container) bool {
	for _, mount := range container.Mounts {
		if mount.Name == volume && mount.Driver == "dvol" {
			return true
		}
	}
	return false
}

func NewDockerRuntime() *DockerRuntime {
	client, _ := docker.NewClientFromEnv()
	stopped := make(map[string]map[ContainerID]ContainerName)
	return &DockerRuntime{client, stopped}
}

// Related determines which containers are related to a particular volume.
// A container is deemed to be related if a dvol volume with the same name appears
// in the Mounts information for a container which is also currently running.
// Related returns an array of related container names and any error encountered.
func (runtime *DockerRuntime) Related(volume string) ([]Container, error) {
	relatedContainers := make([]Container, 0)
	containers, err := runtime.client.ListContainers(docker.ListContainersOptions{})
	if err != nil {
		return relatedContainers, err
	}
	for _, c := range containers {
		container, err := runtime.client.InspectContainer(c.ID)
		if err != nil {
			return relatedContainers, err
		}
		if isRelated(volume, container) && container.State.Running {
			relatedContainers = append(relatedContainers, Container{ID: ContainerID(container.ID), Name: ContainerName(container.Name)})
		}
	}
	return relatedContainers, nil
}

func (runtime *DockerRuntime) Start(volume string) error {
	if value := runtime.stopped[volume]; value == nil {
		return fmt.Errorf("never locked %s, can't unlock it", volume)
	}

	for cid := range runtime.stopped[volume] {
		if err := runtime.client.StartContainer(string(cid), nil); err != nil {
			return err
		}
		delete(runtime.stopped[volume], cid)
	}
	return nil
}

func (runtime *DockerRuntime) attemptStop(cid ContainerID) error {
	var err error
	for idx := 0; idx < 10; idx++ {
		// TODO: Need the ID here so refactoring neccesary
		if err = runtime.client.StopContainer(string(cid), 10); err == nil {
			return nil
		}
		// Log that we're retrying
	}
	// Log that we failed to stop the container
	return err
}

func (runtime *DockerRuntime) Stop(volume string) error {
	if value := runtime.stopped[volume]; value != nil {
		return fmt.Errorf("%s already locked so can't lock it", volume)
	}
	relatedContainers, err := runtime.Related(volume)
	if err != nil {
		return err
	}
	runtime.stopped[volume] = make(map[ContainerID]ContainerName)

	for _, container := range relatedContainers {
		// Attempt to stop the container using the client
		runtime.attemptStop(container.ID)
		runtime.stopped[volume][container.ID] = container.Name
	}

	return nil
}

func (runtime *DockerRuntime) Remove(volume string) error {
	return nil
}
