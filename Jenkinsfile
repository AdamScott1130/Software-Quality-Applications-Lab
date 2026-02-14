pipeline {
  agent any

  environment {
    HEADLESS = "true"
  }

  stages {

    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Start Keycloak (Docker Compose)') {
      steps {
        dir('qa-automation-project-keycloak') {
          sh 'docker compose up -d'
          sh 'sleep 20'
        }
      }
    }

    stage('API Tests (Newman)') {
      steps {
        dir('qa-automation-project-keycloak/api-tests') {
          sh 'npm ci'
          sh '''
            npx newman run collections/Keycloak_QA_Tests.postman_collection.json \
              -r cli,junit --reporter-junit-export target/newman.xml
          '''
        }
      }
      post {
        always {
          junit 'qa-automation-project-keycloak/api-tests/target/newman.xml'
        }
      }
    }

    stage('UI Tests (Selenium + TestNG)') {
      steps {
        // your Maven project is nested (keycloak-ui-tests/keycloak-ui-tests)
        dir('keycloak-ui-tests/keycloak-ui-tests') {
          sh 'mvn -q clean test'
        }
      }
      post {
        always {
          junit 'keycloak-ui-tests/keycloak-ui-tests/target/surefire-reports/*.xml'
        }
      }
    }
  }

  post {
    always {
      dir('qa-automation-project-keycloak') {
        sh 'docker compose down -v'
      }
    }
  }
}
