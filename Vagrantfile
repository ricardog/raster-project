Vagrant.configure("2") do |config|
  config.vm.define :cli do |cli|
    cli.vm.synced_folder '.', '/vagrant', disabled: true
    cli.vm.provider "docker" do |d|
      d.name = "predicts"
      d.build_dir = "."
      d.build_args = ['-t', 'predicts:4.0.0']
      #d.create_args = ['--gpus', 'all']
      d.env = {PASSWORD: 'browsesafely'}
      d.ports = ['8787:8787', '8888:8888']
      d.volumes = ["datasets:/data",
                   "predicts-data:/out"
                  ]
      d.force_host_vm = false
      if false
        d.vagrant_vagrantfile = "/Users/ricardog/tmp/Vagrantfile"
        d.force_host_vm = true
        d.host_vm_build_dir_options = {type: 'rsync',
                                       rsync__exclude: ".git/"
                                      }
      end
    end
  end
end

