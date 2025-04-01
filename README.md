# RESTful API for Vehicle Diagnosis Simulation

## Overview
This project models a vehicle diagnosis API that interacts with a virtual ECU (Electronic Control Unit) implemented in Python. The API allows control over engine parameters, communication, security management, power supply, and error injection. Built with Flask-RESTful, it supports standard HTTP methods (GET, POST, PUT, DELETE). 

A LabVIEW client interface has been developed for real-time testing and visualization.

## API Features
- **API KEY** - Send it into the request header to enable communication with the API.
- **GET** - Get info about vehciule state like engine params, supply voltage, security access and error manager.
- **POST** - Inject error into the system.
- **PUT** - Modify engine or voltage params, change gear or increase thortle, start/stop the engine
- **DELETE** - Delete error memory, error input or error logs as a whole or for specific params
  
## Virtual ECU Features
- **Engine Parameters** – Read and modify engine performance metrics.
- **Communication** – Simulate vehicle communication protocols.
- **Security Management** – Implement authentication and access control mechanisms (seed: 4 digits + 15 random digits -> key: 4 digits + 15 random digits sum for each random digit must be 10 between seed and key in order to valide authentification to the ECU).
- **Power Supply** – Monitor and adjust voltage levels.
- **Error Injection** – Simulate and test error-handling mechanisms.

## LabVIEW Client
The LabVIEW client provides an interactive front-end for testing the API:

### Control Panel  
- **Engine Parameters** – Off.
![Control Panel](https://github.com/user-attachments/assets/0fcdc2a4-6543-47e0-a800-2285d3eaf1bf)
- **Engine Parameters** – and with measurement on.
![Control Panel Meas](https://github.com/user-attachments/assets/3606b485-6030-4606-a3a6-83956517df26)


### Block Diagram  
![Block Diagram](https://github.com/user-attachments/assets/fbcaee6d-37c6-4fe6-a282-9ded2d86accc)

### Virtual ECU Design 
![EcuFlowDiagram](https://github.com/user-attachments/assets/3c1d5ad6-915b-43d7-9383-c3ad2df9f9e7)





