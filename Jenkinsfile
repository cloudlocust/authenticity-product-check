pipeline {
  agent {
    label "jenkins-jenkins-python3-11"
  }
  environment {
    // GEnerate random number between 0 and 1000
    ID = "${Math.abs(new Random().nextInt(1000+1))}"
    // Do not change this env var name, it's used in tests env vars
    //    DB_HOST = "postgresql"
    //    RABBITMQ_HOST = "rabbitmq"
    //    BACKBONE_RABBITMQ_HOST = "backbone-rabbitmq"
    //            DISCORD_WEBHOOK_URL = credentials('discord-webhook')
    //            GITHUB_CREDENTIALS = credentials('github myem developer')
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
                sh "kubectl wait --for=condition=ready pod/postgresql-0 --timeout=1000s --namespace testing-${ID}"
                sh '''#!/bin/bash
                export PORT_DB=$(kubectl get -o jsonpath="{.spec.ports[0].nodePort}" services postgresql -n testing-${ID})
                '''
                sh '''#!/bin/bash
                echo $PORT_DB
                '''

              }
            }
          }
        }
      }
    }
        stage('unit and integration tests'){
            steps('Unit test'){
                sh '''#!/bin/bash
                kubectl wait --for=condition=ready pod postgresql-0 --timeout=120s --namespace testing-${ID}
                export HOSTNAME_DB=$(kubectl get pods --selector=app.kubernetes.io/instance=postgresql -o jsonpath='{.items[].spec.nodeName}' -n testing-${ID})
                export ADDRESS_DB=$(kubectl get nodes --selector=kubernetes.io/hostname=${HOSTNAME_DB} -o jsonpath='{.items[].status.addresses[?(@.type=="InternalIP")].address}' -n testing-${ID})
                export PORT_DB=$(kubectl get -o jsonpath="{.spec.ports[0].nodePort}" services postgresql -n testing-${ID})
                export DB_HOST=${ADDRESS_DB}:${PORT_DB}
                echo $DB_HOST
                pipenv run coverage run --source=authenticity_product --concurrency=eventlet -m pytest -x -v --junit-xml=reports/report.xml  tests && pipenv run coverage xml
                '''
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
