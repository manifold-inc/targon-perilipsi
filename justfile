build:
  docker build -t manifoldlabs/sn4-perilipsi .

run: build
  docker run -p 8001:8001 --env-file .env -d --name dev_image manifoldlabs/sn4-perilipsi

# Alias for the run command
up: run
