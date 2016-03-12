package containers

import (
	"github.com/fsouza/go-dockerclient"
)

type DockerRuntime struct {
	Client *docker.Client
}

func (r DockerRuntime) isRelated(volume string, container *docker.Container) bool {
	for _, mount := range container.Mounts {
		if mount.Name == volume && mount.Driver == "dvol" {
			return true
		}
	}
	return false
}

func (runtime DockerRuntime) Related(volume string) ([]string, error) {
	containers, _ := runtime.Client.ListContainers(docker.ListContainersOptions{})
	relatedContainers := make([]string, 0)
	for _, container := range containers {
		cont, _ := runtime.Client.InspectContainer(container.ID)
		if runtime.isRelated(volume, cont) && cont.State.Running {
			relatedContainers = append(relatedContainers, cont.Name)
		}
	}
	return relatedContainers, nil
}

func (runtime DockerRuntime) Start(volume string) error {
	return nil
}

func (runtime DockerRuntime) Stop(volume string) error {
	return nil
}

func (runtime DockerRuntime) Remove(volume string) error {
	return nil
}
