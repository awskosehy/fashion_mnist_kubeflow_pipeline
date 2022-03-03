# tensorboard component structure

    src/*            # tensorboard componenet source code files
    tests/*          # Unit tests
    run_tests.sh     # Small script that runs the tests
    README.md        # Documentation for tensorboard component.

    Dockerfile       # Dockerfile to build the threei/kfp_tensorboard:latest container image
    build_image.sh   # Small script that runs docker build and docker push

    component.yaml   # tensorboard component definition in YAML format