package containers

import (
	"github.com/fsouza/go-dockerclient"
)

type DockerRuntime struct {
	Client *docker.Client
}

func isRelated(volume string, container *docker.Container) bool {
	for _, mount := range container.Mounts {
		if mount.Name == volume && mount.Driver == "dvol" {
			return true
		}
	}
	return false
}

func (runtime DockerRuntime) Related(volume string) ([]string, error) {
	relatedContainers := make([]string, 0)
	containers, err := runtime.Client.ListContainers(docker.ListContainersOptions{})
	if err != nil {
		return relatedContainers, err
	}
	for _, c := range containers {
		container, err := runtime.Client.InspectContainer(c.ID)
		if err != nil {
			return relatedContainers, err
		}
		if isRelated(volume, container) && container.State.Running {
			relatedContainers = append(relatedContainers, container.Name)
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
