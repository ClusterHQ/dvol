package containers

type NoneRuntime struct{}

func NewNoneRuntime() *NoneRuntime {
	return &NoneRuntime{}
}

func (runtime *NoneRuntime) Related(string) ([]Container, error) {
	return []Container{}, nil
}

func (runtime *NoneRuntime) Start(string) error {
	return nil
}

func (runtime *NoneRuntime) Stop(string) error {
	return nil
}

func (runtime *NoneRuntime) Remove(string) error {
	return nil
}
