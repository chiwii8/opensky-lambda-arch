help: ## show the help
	@echo " Available Commands:"
	@echo " make up				- Start the stack in dettach mode"
	@echo " make up-kappa		- Start the aditional stack in dettach mode"
	@echo " make build			- Build and start the stack in dettach mode"
	@echo " make build-kappa	- Build and start the aditional stack in dettach mode"
	@echo " make down			- Stop and delete the stack"
	@echo " make down-kappa		- Build and start the aditional stack in dettach mode"
	@echo " make undeploy   	- Stop and delete the stack with the volume created"


up:
	docker compose up -d

up-kappa:
	docker compose -f docker-compose-kappa.yml up -d 

build: 
	docker compose up -d --build

build-kappa:
	docker compose -f docker-compose-kappa.yml up -d --build

down:
	docker compose down

down-kappa:
	docker compose -f docker-compose-kappa.yml down

undeploy:
	docker compose down -v


