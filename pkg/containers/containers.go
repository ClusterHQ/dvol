package containers

type Containers interface {
	Related(string) ([]string, error)
	Start(string) error
	Stop(string) error
	Remove(string) error
}
