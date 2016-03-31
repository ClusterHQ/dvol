package containers

type ContainerID string
type ContainerName string

type Container struct {
	ID   ContainerID
	Name ContainerName
}

type Runtime interface {
	Related(string) ([]Container, error)
	Start(string) error
	Stop(string) error
	Remove(string) error
}
