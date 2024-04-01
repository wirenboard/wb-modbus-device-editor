@Library('wbci@feature/release-any-file')
buildDebSbuild(
    // customReleaseBranchPattern: '^tmp/test-gh-release$',
    defaultTargets: 'bullseye-host',
    repos: ['devTools'],
    defaultRunLintian: true,
    defaultRunPythonChecks: true,
    customBuildSteps: {
        stage("Build exe") {
            sh 'docker run -t -v $DEV_VOLUME -w $PWD/$PROJECT_SUBDIR tobix/pywine bash -c "./Build.sh clean &&  ./Build.sh windows"'
            sh "cp -r $PROJECT_SUBDIR/dist/ $RESULT_SUBDIR/"
            archiveArtifacts artifacts: "$RESULT_SUBDIR/dist/windows/*.exe"
        }
    }
)
