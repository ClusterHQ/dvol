package containers

import (
	"github.com/fsouza/go-dockerclient"
)

type DockerRuntime struct {
	Client *docker.Client
}

func (runtime DockerRuntime) Related(volume string) ([]string, error) {
	containers, _ := runtime.Client.ListContainers(docker.ListContainersOptions{})
	relatedContainers := make([]string, 0)
	for _, container := range containers {
		cont, _ := runtime.Client.InspectContainer(container.ID)
		if cont.HostConfig.VolumeDriver == "dvol" || cont.Config.VolumeDriver == "dvol" {
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
