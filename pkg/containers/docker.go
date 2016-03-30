package containers

import (
	"fmt"

	"github.com/fsouza/go-dockerclient"
)

type DockerRuntime struct {
	client  *docker.Client
	stopped map[string]map[string]string
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
	stopped := make(map[string]map[string]string)
	return &DockerRuntime{client, stopped}
}

// Related determines which containers are related to a particular volume.
// A container is deemed to be related if a dvol volume with the same name appears
// in the Mounts information for a container which is also currently running.
// Related returns an array of related container names and any error encountered.
func (runtime *DockerRuntime) Related(volume string) ([]string, error) {
	relatedContainers := make([]string, 0)
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
			relatedContainers = append(relatedContainers, container.Name)
		}
	}
	return relatedContainers, nil
}

func (runtime *DockerRuntime) Start(volume string) error {
	if value := runtime.stopped[volume]; value == nil {
		return fmt.Errorf("never locked %s, can't unlock it", volume)
	}

	for _, container := range runtime.stopped[volume] {
		if err := runtime.client.StartContainer(container, nil); err != nil {
			return err
		}
		delete(runtime.stopped, container)
	}
	return nil
}

func (runtime *DockerRuntime) attemptStop(containerID string) error {
	var err error
	for idx := 0; idx < 10; idx++ {
		// TODO: Need the ID here so refactoring neccesary
		if err = runtime.client.StopContainer("d47d5f5a5f41", 10); err == nil {
			return nil
		}
		// Log that we're retrying
	}
	// Log that we failed to stop the container
	return err
}

func (runtime *DockerRuntime) Stop(volume string) error {
	_ = "breakpoint"
	if value := runtime.stopped[volume]; value != nil {
		return fmt.Errorf("%s already locked so can't lock it", volume)
	}
	relatedContainers, err := runtime.Related(volume)
	if err != nil {
		return err
	}
	runtime.stopped[volume] = make(map[string]string)

	for _, container := range relatedContainers {
		// Attempt to stop the container using the client
		runtime.attemptStop(container)
		runtime.stopped[volume][container] = container
	}

	return nil
}

func (runtime *DockerRuntime) Remove(volume string) error {
	return nil
}
