# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.network "forwarded_port", guest: 8000, host: 8080
  config.vm.provision "shell", inline: <<-SHELL

  SHELL
  config.vm.provision :shell, :path => "provision.sh"
end
