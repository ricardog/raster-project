Vagrant.configure("2") do |config|
  config.vm.define :cli do |cli|
    cli.vm.synced_folder '.', '/vagrant', disabled: true
    cli.vm.provider "docker" do |d|
      d.build_dir = "."
      d.build_args = ['-t', 'predicts:latest']
      d.env = {PASSWORD: 'browsesafely'}
      d.ports = ['8787:8787']
      d.volumes = ["/home/ricardog/src/eec/predicts/data:/data:ro",
                   "predicts-data:/out"
                  ]
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

