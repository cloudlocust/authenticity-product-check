pipeline{
    agent { label "jenkins-jenkins-python3-11" }
    environment{
           // GEnerate random number between 0 and 1000
           ID = "${Math.abs(new Random().nextInt(1000+1))}"
           // Do not change this env var name, it's used in tests env vars
        //    DB_HOST = "postgresql"
        //    RABBITMQ_HOST = "rabbitmq"
        //    BACKBONE_RABBITMQ_HOST = "backbone-rabbitmq"
           DISCORD_WEBHOOK_URL = credentials('discord-webhook')
           GITHUB_CREDENTIALS = credentials('github myem developer')
    }


    stages{

        stage('Static code analysing') {
            stages {
                stage('Install dependencies')
                {
                    steps {
                        sh 'pipenv --rm || exit 0'
                        sh 'pipenv install --pre --dev'
                    }
                }
                stage ('PyDocStyle') {
                    steps {
                        sh 'pipenv run pydocstyle --config=.pydocstyle.ini ${MODULE_DIR_NAME}'
                    }
                }

                stage ('Mypy') {
                    steps {
                        sh 'pipenv run mypy -p customer_center --config-file mypy.ini --no-incremental'
                    }
                }

                stage ('Pylint') {
                    steps {
                        sh 'pipenv run pylint customer_center --output-format=parseable  --rcfile=.pylintrc'
                    }
                }
            }
        }

        stage('Create a namespace and start the Postgresql and Rabbitmq instances '){
            stages{
                stage("Create the namespace and add the bitnami helm repository"){
                    steps{
                        script{
                            withKubeConfig([credentialsId:'kubernetes_test',]) {
                                sh "helm repo add bitnami https://charts.bitnami.com/bitnami"
                                sh "kubectl create namespace testing-${ID}"
                            }
                        }
                    }
                }

                stage("Install the Postgresql helm chart"){
                    steps{
                        script{
                            withKubeConfig([credentialsId:'kubernetes_test']) {
                                sh "helm install postgresql bitnami/postgresql -f tests/postgresql.yaml --namespace testing-${ID}"
                            }
                        }
                    }
                }

                stage("Install the Backbone Rabbitmq helm chart"){
                    steps{
                        script{
                            withKubeConfig([credentialsId:'kubernetes_test']) {
                                sh "helm upgrade --install backbone-rabbitmq bitnami/rabbitmq -f tests/rabbitmq.yaml --namespace=testing-${ID} --version 14.0.1"
                            }
                        }
                    }
                }

                stage("Install the BL Rabbitmq helm chart"){
                    steps{
                        script{
                            withKubeConfig([credentialsId:'kubernetes_test']) {
                                sh "helm install rabbitmq bitnami/rabbitmq -f tests/rabbitmq.yaml --namespace testing-${ID} --version 14.0.1"
                            }
                        }
                    }
                }
            }
        }

        stage('unit and integration tests'){
            steps('Unit test'){
                sh '''#!/bin/bash
                kubectl wait --for=condition=ready pod postgresql-0 --timeout=120s --namespace testing-${ID} && kubectl wait --for=condition=ready pod backbone-rabbitmq-0 --timeout=120s --namespace testing-${ID} && kubectl wait --for=condition=ready pod rabbitmq-0 --timeout=120s --namespace testing-${ID}
                export RABBITMQ_HOSTNAME=$(kubectl get pods --selector=app.kubernetes.io/instance=rabbitmq -o jsonpath='{.items[].spec.nodeName}' -n testing-${ID})
                export RABBITMQ_HOST=$(kubectl get nodes --selector=kubernetes.io/hostname=${RABBITMQ_HOSTNAME} -o jsonpath='{.items[].status.addresses[?(@.type=="InternalIP")].address}' -n testing-${ID})
                export RABBITMQ_API_PORT=$(kubectl get -o jsonpath="{.spec.ports[?(@.name=='http-stats')].nodePort}" services rabbitmq -n testing-${ID})
                export RABBITMQ_AMQP_PORT=$(kubectl get -o jsonpath="{.spec.ports[?(@.name=='amqp')].nodePort}" services rabbitmq -n testing-${ID})
                export BACKBONE_RABBITMQ_HOSTNAME=$(kubectl get pods --selector=app.kubernetes.io/instance=backbone-rabbitmq -o jsonpath='{.items[].spec.nodeName}' -n testing-${ID})
                export BACKBONE_RABBITMQ_HOST=$(kubectl get nodes --selector=kubernetes.io/hostname=${BACKBONE_RABBITMQ_HOSTNAME} -o jsonpath='{.items[].status.addresses[?(@.type=="InternalIP")].address}' -n testing-${ID})
                export BACKBONE_RABBITMQ_API_PORT=$(kubectl get -o jsonpath="{.spec.ports[?(@.name=='http-stats')].nodePort}" services backbone-rabbitmq -n testing-${ID})
                export BACKBONE_RABBITMQ_AMQP_PORT=$(kubectl get -o jsonpath="{.spec.ports[?(@.name=='amqp')].nodePort}" services backbone-rabbitmq -n testing-${ID})
                export HOSTNAME_DB=$(kubectl get pods --selector=app.kubernetes.io/instance=postgresql -o jsonpath='{.items[].spec.nodeName}' -n testing-${ID})
                export ADDRESS_DB=$(kubectl get nodes --selector=kubernetes.io/hostname=${HOSTNAME_DB} -o jsonpath='{.items[].status.addresses[?(@.type=="InternalIP")].address}' -n testing-${ID})
                export PORT_DB=$(kubectl get -o jsonpath="{.spec.ports[0].nodePort}" services postgresql -n testing-${ID})
                export DB_HOST=${ADDRESS_DB}:${PORT_DB}
                echo $DB_HOST
                echo $RABBITMQ_HOST:$RABBITMQ_AMQP_PORT
                pipenv run coverage run --source=customer_center --concurrency=eventlet -m pytest -x -v --junit-xml=reports/report.xml  tests && pipenv run coverage xml
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
            when {
                expression { BRANCH_NAME ==~ /(production|master|develop)/ }
            }
                     stages {
           stage('Publish in dockerhub'){
            environment {
                registryCredential = 'dockerhub'
                app_regisgtry = 'myem/customer-center'
                ENV_NAME = getEnvName(BRANCH_NAME)
                VERSION= "${BUILD_NUMBER}"
            }
            steps{
               script {
                    docker.withRegistry( '', registryCredential ) {
                        // we copy files inside the app image and tag it
                        def appimage = docker.build(app_regisgtry + ":${ENV_NAME}", "--no-cache . -f ci/Dockerfile --build-arg GITHUB_CREDENTIALS=$GITHUB_CREDENTIALS " )
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
        stage('Publish in chart regisry'){
                       when{
                        expression { BRANCH_NAME ==~ /(production|master|develop)/ }
                        expression { changeset('customer-center-chart')}
                        }
                       environment {
                           ENV_NAME = getEnvName(BRANCH_NAME)
                           VERSION_CHART = "0.1.${BUILD_NUMBER}"
                           USER_NAME_ = credentials('helm_registry_username')
                           PASSWORD_ = credentials('helm_registry_password')
                           url = credentials('helm_registry_url')
                           URL_ = "${url}/${ENV_NAME}registry"
                           }
                        steps {
                              script{

                                sh(script: " helm registry login -u ${USER_NAME_} -p ${PASSWORD_} ${URL_} ")
                                sh(script: "rm -rf helm-chart-repository")
                                sh(script: "mkdir helm-chart-repository")
                                sh(script: "helm package customer-center-chart --version ${VERSION_CHART} -d helm-chart-repository")
                                sh(script: "helm push helm-chart-repository/* oci://${URL_}")
                                sh(script: "rm -rf helm-chart-repository")

                }
              }

                }
       stage ('Deploy') {
        when {
                expression { BRANCH_NAME ==~ /(master|develop|production)/ }
           }
        environment {
              ENV_NAME = getEnvName(BRANCH_NAME)
              USER_NAME_ = credentials('helm_registry_username')
              PASSWORD_ = credentials('helm_registry_password')
              url = credentials('helm_registry_url')
              URL_ = "${url}/${ENV_NAME}registry"

           }
            steps {
                script{
                    // The below will clone network devops repository
                    git([url: 'https://github.com/myenergymanager/network-devops', branch: "master", credentialsId: 'github myem developer'])
                    // Checkout to master


                    sh " helm registry login -u ${USER_NAME_} -p ${PASSWORD_} ${URL_} "
                    // This will apply new helm upgrade, you need to specify namespace.

                     withKubeConfig([credentialsId:'kubernetes_staging-alpha-preprod', contextName: "ng${ENV_NAME}"]) {
                        sh "sh ./deployments-scripts/deploy.sh customer-center ng${ENV_NAME} ${URL_}"

                    }
                }
            }
            post {
                success{
                    discordSend (description: "Jenkins ${ENV_NAME} Pipeline Build Success", footer: "customer-center offers service has been deployed", link: env.BUILD_URL, result: currentBuild.currentResult, title: JOB_NAME, webhookURL: "${DISCORD_WEBHOOK_URL}")
                }
                failure{
                    discordSend (description: "Jenkins ${ENV_NAME} Pipeline Build Failed", footer: "there was an error  in the customer-center service deployment", link: env.BUILD_URL, result: currentBuild.currentResult, title: JOB_NAME, webhookURL: "${DISCORD_WEBHOOK_URL}")
                }
            }
       }
    }
    post{
        always{
            script {
                try {
                    git credentialsId: 'github myem developer', url: 'https://github.com/myenergymanager/customer-center-microservice'
                    echo "build finished"
                    withKubeConfig([credentialsId:'kubernetes_test']) {
                        sh "helm delete postgresql backbone-rabbitmq rabbitmq --namespace testing-${ID}"
                        sh"kubectl wait --for=delete pod/postgresql-0 --timeout=60s && kubectl wait --for=delete pod/backbone-rabbitmq-0 --timeout=60s && kubectl wait --for=delete pod/rabbitmq-0 --timeout=60s"
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
     if(branchName == "master")  {
         return "alpha";
     }
     // production branch is deployed manually in prod and automatically in preprod.
     else if (branchName == "production"){
         return "preprod";
     }
     else {
         return "staging";
     }
}

def allChangeSetsFromLastSuccessfulBuild() {
    def jobName="$JOB_NAME"
    def job = Jenkins.getInstance().getItemByFullName(jobName)
    def lastSuccessBuild = job.lastSuccessfulBuild.number as int
    def currentBuildId = "$BUILD_ID" as int

    def changeSets = []

    for(int i = lastSuccessBuild + 1; i < currentBuildId; i++) {
        echo "Getting Change Set for the Build ID : ${i}"
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

def isPathExist(changeSets,path) {

            b = false
            changeSets.each {
                a = it.startsWith(path)
                b = a || b
            }
            return b


}

def changeset(path){
    def jobName="$JOB_NAME"
    def job = Jenkins.getInstance().getItemByFullName(jobName)
    if ( job.lastSuccessfulBuild == null) { return true }
    def changeSets = allChangeSetsFromLastSuccessfulBuild()
    return  isPathExist(getFilesChanged(changeSets),path)

}


def isJustPathExist(changeSets,path) {

            b = true
            changeSets.each {
                a = it.startsWith(path)
                b = a && b
            }
            return b


}