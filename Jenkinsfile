buildDebSbuild(
    defaultTargets: 'bullseye-host',
    repos: ['devTools'],
    defaultRunLintian: true,
    defaultRunPythonChecks: true,
    releaseFilesFilter: "**/*.deb, **/*.zip",
    customBuildSteps: {
        stage("Build exe") {
            sh 'docker run -t -v $DEV_VOLUME -w $PWD/$PROJECT_SUBDIR tobix/pywine:3.10 bash -c "./Build.sh clean &&  ./Build.sh windows"'
            sh 'wbdev root bash -c "cd $PROJECT_SUBDIR/dist/windows && zip -r wb-modbus-device-editor-windows.zip ./wb-modbus-device-editor/"'
            sh "cp -r $PROJECT_SUBDIR/dist/ $RESULT_SUBDIR/"
            archiveArtifacts artifacts: "$RESULT_SUBDIR/dist/windows/*.zip"
        }
        stage("Build appimage") {
            sh 'wbdev root bash -c "apt-get update && apt-get install python3-tk -y && ./Build.sh clean &&  ./Build.sh linux"'
        }
    }
)
