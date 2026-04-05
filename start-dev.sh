sudo sysctl -w kern.maxfiles=131072
sudo sysctl -w kern.maxfilesperproc=65536
ulimit -n 65536 &&   source ~/.nvm/nvm.sh && nvm use 24 && yarn start

