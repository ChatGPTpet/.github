
# ChatGPTFirewall

![Logo](images/logo_small.png)

## Description

ChatGPTFirewall is a web-based application that allows users to interact with their data through a conversational interface. This project leverages the power of vector databases and large language models to enable users to upload files, ask questions in natural language, and receive contextual answers.

## How It Works

ChatGPTFirewall provides a secure platform for users to upload text documents and query them using natural language. The application processes these documents, converting them into vectorized forms that are stored and indexed. Users can then interact with the data, ask questions, and receive relevant responses that are generated by the system's integrated language model.

## Features

- **Conversational Data Interaction**: Users can chat with their data by uploading files and asking questions in natural language.
- **File Upload Support**: Manual file uploads.
- **Vector Database Integration**: Utilizes Qdrant for efficient similarity searches on text data.
- **Editable Responses**: Adjust the number of sentences returned from searches.
- **Customizable Prompts**: Customize the prompts sent to ChatGPT for tailored answers.
- **Authentication**: Secure user login with Auth0.
- **File Management**: Easily manage your uploaded files.
- **Demo Mode**: Explore the application's capabilities with preloaded files in demo mode.
- **Multilingual**: The application supports both German and English languages.
- **Rooms**: Create different rooms for different contexts.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- Docker and Docker Compose are installed on your machine.
- You have an OpenAI API key if you wish to use the ChatGPT response features.

## Installation

Follow these steps to install and run ChatGPTFirewall:

1. **Clone this repository:**
   ##### SSH
   ```sh
   git clone git@github.com:ChatGPTfirewall/ChatGPTfirewall.git
   ```
   ##### HTTPS
   ```sh
   git clone https://github.com/ChatGPTfirewall/ChatGPTfirewall.git
   ```

2. **Navigate to the project directory:**
   ```sh
   cd ChatGPTfirewall
   ```

3. **Configure Auth0 Settings:**
   Create a single page application, a custom API, and a machine-to-machine application in your Auth0 tenant. You will need the domain and audience from these settings for the next steps.

4. **Create and configure the `.env` file:**
   ```sh
   cp .env.example .env
   ```
   Edit the `.env` file and adjust the variables to your needs. Set the `OPEN_AI_KEY` with your OpenAI API key to enable ChatGPT responses. Define the `VITE_*` environment variables according to your setup. For Auth0 configuration, set `JWT_AUDIENCE` to the identifier of your Auth0 API and `JWT_ISSUER` to your Auth0 domain, both of which can be found in your Auth0 dashboard.

5. **Build and start the application:**
   ```sh
   docker compose up --build
   ```
   The application should now be running at [http://localhost:5173/](http://localhost:5173/).

## Further Configuration and Commands

Enter the backend container and navigate to the required folder to execute backend-related commands:

```sh
docker exec -it backend /bin/bash
cd /chat_with_your_data
```

Here are some useful commands you can run:

- Autogenerate database migrations:
  ```sh
  python manage.py makemigrations
  ```
- Apply migrations to the database:
  ```sh
  python manage.py migrate
  ```
- Manage demo users:
  ```sh
  python manage.py create_demo_users
  python manage.py delete_demo_users
  ```

## Acknowledgments

This application was developed as part of a research project for our Master's degree in Applied Computer Science by Robert Pfeiffer, Jens-Uwe Hennings, and Mats Klein, under the guidance of Professor Sebastian Gajek. We are grateful for the support and resources provided by Sebastian Gajek and Hochschule Flensburg, which made this project possible.