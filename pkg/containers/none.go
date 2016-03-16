package containers

type NoneRuntime struct{}

func (NoneRuntime) Related(string) ([]string, error) {
	return []string{}, nil
}

func (NoneRuntime) Start(string) error {
	return nil
}

func (NoneRuntime) Stop(string) error {
	return nil
}

func (NoneRuntime) Remove(string) error {
	return nil
}
