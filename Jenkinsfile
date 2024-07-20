pipeline {
  agent {
    label "jenkins-jenkins-python3-11"
  }
  environment {
    // GEnerate random number between 0 and 1000
    ID = "${Math.abs(new Random().nextInt(1000+1))}"
  }

  stages {

    stage('Static code analysing') {
      stages {
        stage('Install dependencies') {
          steps {
            sh 'pipenv --rm || exit 0'
            sh 'pipenv install --pre --dev'
          }
        }
        stage('PyDocStyle') {
          steps {
            sh 'pipenv run pydocstyle --config=.pydocstyle.ini ${MODULE_DIR_NAME}'
          }
        }
        stage('Mypy') {
          steps {
            sh 'pipenv run mypy -p user_management --config-file mypy.ini --no-incremental  --namespace-packages'
          }
        }

        stage('Pylint') {
          steps {
            sh 'pipenv run pylint user_management --output-format=parseable  --rcfile=.pylintrc'
          }

      }
    }
    stage('Create a namespace and start the Postgresql instances ') {
      stages {
        stage("Create the namespace and add the bitnami helm repository") {
          steps {
            script {
              withKubeConfig([credentialsId: 'kubernetes_test', ]) {
                sh "helm repo add bitnami https://charts.bitnami.com/bitnami"
                sh "kubectl create namespace testing-${ID}"
              }
            }
          }
        }

        stage("Install the Postgresql helm chart") {
          steps {
            script {
              withKubeConfig([credentialsId: 'kubernetes_test']) {
                sh "helm install postgresql bitnami/postgresql -f tests/postgresql.yaml --namespace testing-${ID} || true"
              }
            }
          }
        }
      }
    }
    stage('unit and integration tests') {
      steps('Unit test') {
        sh '''
        #!/bin/bash
        kubectl wait --for=condition=ready pod postgresql-0 --timeout=120s --namespace testing-${ID}
        export DB_HOST="postgresql.testing-${ID}.svc:5432"
        pipenv run coverage run --source=authenticity_product --concurrency=eventlet -m pytest -x -v --junit-xml=reports/report.xml  tests && pipenv run coverage xml
        '''
      }
    }

    stage('build && SonarQube analysis') {
      environment {
        scannerHome = tool 'SonarQubeScanner'
      }
      steps {
        withSonarQubeEnv('sonarqube') {
          sh "echo $PATH & echo $JAVA_HOME"
          sh "${scannerHome}/bin/sonar-scanner"
        }
      }
    }

    stage("Quality Gate") {
      steps {
        script {
          timeout(time: 5, unit: 'MINUTES') {
            def qg = waitForQualityGate() // Reuse taskId previously collected by withSonarQubeEnv
            if (qg.status != 'OK') {
              error "Pipeline aborted due to quality gate failure: ${qg.status}"
            }
          }
        }
      }
    }
    stage("Publish") {
        when{
             expression { BRANCH_NAME ==~ /(master|develop|production)/ }
        }
      stages {
        stage('Publish in dockerhub') {
          environment {
            registryCredential = 'dockerhub'
            app_regisgtry = 'khaldi22/authenticity_product'
            ENV_NAME = getEnvName(BRANCH_NAME)
            VERSION = "${BUILD_NUMBER}"
          }
          steps {
            script {
              docker.withRegistry('', registryCredential) {
                // we copy files inside the app image and tag it
                def appimage = docker.build(app_regisgtry + ":${ENV_NAME}", "--no-cache . -f ci/Dockerfile ")
                appimage.push("${ENV_NAME}")
                if (env.BRANCH_NAME == "production") {
                  appimage.push("${ENV_NAME}-${VERSION}")
                }
              }
              // Clean up unused Docker resources older than 1 hour
              sh 'docker system prune -af --filter "until=1h"'
            }
          }

        }
      }
    }
       stage ('Deploy') {
        when{
             expression { BRANCH_NAME ==~ /(master|develop|production)/ }
        }
        environment {
              ENV_NAME = getEnvName(BRANCH_NAME)
           }
            steps{
                script{
                     withKubeConfig([credentialsId:'kubernetes_test']){
                        sh "helm upgrade --install  authenticity-product  authenticity-product-chart/ -f helm_values/${ENV_NAME}/authenticity-product.yaml -n ${ENV_NAME}"
                     }
                }
            }
       }
  }
  post {
    always {
      script {
        try {
          echo "build finished"
          withKubeConfig([credentialsId: 'kubernetes_test']) {
            sh "helm delete postgresql  --namespace testing-${ID}"
            sh "kubectl wait --for=delete pod/postgresql-0 --timeout=120s --namespace testing-${ID}"
            sh "kubectl delete namespace testing-${ID}"
          }
          junit 'reports/*.xml'
        } catch (Exception e) {
          // Handle the exception (e.g., print an error message, log, etc.)
          echo "An exception occurred: ${e.getMessage()}"
        }
      }
    }
  }
}
def getEnvName(branchName) {
  // This function return staging by default.
  if (branchName == "master") {
    return "alpha";
  }
  // production branch is deployed manually in prod and automatically in preprod.
  else if (branchName == "production") {
    return "preprod";
  } else {
    return "staging";
  }
}

def allChangeSetsFromLastSuccessfulBuild() {
  def jobName = "$JOB_NAME"
  def job = Jenkins.getInstance().getItemByFullName(jobName)
  def lastSuccessBuild = job.lastSuccessfulBuild.number as int
  def currentBuildId = "$BUILD_ID" as int

  def changeSets = []

  for (int i = lastSuccessBuild + 1; i < currentBuildId; i++) {
    echo "Getting Change Set for   the Build ID : ${i}"
    def chageSet = job.getBuildByNumber(i).getChangeSets()
    changeSets.addAll(chageSet)
  }
  changeSets.addAll(currentBuild.changeSets) // Add the  current Changeset
  return changeSets
}

def getFilesChanged(chgSets) {
  def filesList = []
  def changeLogSets = chgSets
  for (int i = 0; i < changeLogSets.size(); i++) {
    def entries = changeLogSets[i].items
    for (int j = 0; j < entries.length; j++) {
      def entry = entries[j]
      def files = new ArrayList(entry.affectedFiles)
      for (int k = 0; k < files.size(); k++) {
        def file = files[k]
        filesList.add(file.path)
      }
    }
  }
  return filesList
}

def isPathExist(changeSets, path) {

  b = false
  changeSets.each {
    a = it.startsWith(path)
    b = a || b
  }
  return b

}

def changeset(path) {
  def jobName = "$JOB_NAME"
  def job = Jenkins.getInstance().getItemByFullName(jobName)
  if (job.lastSuccessfulBuild == null) {
    return true
  }
  def changeSets = allChangeSetsFromLastSuccessfulBuild()
  return isPathExist(getFilesChanged(changeSets), path)

}

def isJustPathExist(changeSets, path) {

  b = true
  changeSets.each {
    a = it.startsWith(path)
    b = a && b
  }
  return b

}
