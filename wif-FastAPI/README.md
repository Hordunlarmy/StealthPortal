<picture> <source media="(prefers-color-scheme: dark)" srcset="https://i.imgur.com/6zUUS9V.jpeg"> <source media="(prefers-color-scheme: light)" srcset="https://i.imgur.com/6zUUS9V.jpeg"> <img alt="README image" src="https://i.imgur.com/6zUUS9V.jpeg"> </picture>

## Running with Docker
To run this project using Docker, follow these steps:

1. Build the image:
```
docker build -t stealth-portal-app .
```
2. Run the container:
```
docker run -p 8000:8000 stealth-portal-app
```
