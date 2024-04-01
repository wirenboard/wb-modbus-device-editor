buildDebSbuild(
    defaultTargets: 'bullseye-host',
    repos: ['devTools'],
    defaultRunLintian: true,
    defaultRunPythonChecks: true,
    customBuildSteps: {
        stage("Build exe") {
            sh 'docker run -t -v $DEV_VOLUME -w $PWD/$PROJECT_SUBDIR tobix/pywine bash -c "./Build.sh clean &&  ./Build.sh windows"'
            sh 'wbdev root bash -c "cd $PROJECT_SUBDIR/dist/windows && zip -r wb-modbus-device-editor.zip ./wb-modbus-device-editor/"'
            sh "cp -r $PROJECT_SUBDIR/dist/ $RESULT_SUBDIR/"
            archiveArtifacts artifacts: "$RESULT_SUBDIR/dist/windows/*.zip"
        }
    }
)
