@Library('wbci@tmp/webconn/copyartifacts') _
buildDebSbuild(
    customReleaseBranchPattern: '^tmp/webconn/test-gh-release$',
    defaultTargets: 'bullseye-host',
    repos: ['devTools'],
    defaultRunLintian: true,
    defaultRunPythonChecks: true,
    releaseFilesFilter: '**/*.deb, **/*.exe',
    customBuildSteps: {
        stage("Build exe") {
            sh 'docker run -t -v $DEV_VOLUME -w $PWD/$PROJECT_SUBDIR tobix/pywine bash -c "./Build.sh clean &&  ./Build.sh windows"'
            sh "cp -r $PROJECT_SUBDIR/dist/ $RESULT_SUBDIR/"
            archiveArtifacts artifacts: "$RESULT_SUBDIR/dist/windows/*.exe"
        }
    }
)
