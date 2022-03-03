# model_path component structure

    src/*            # model_path component source code files
    tests/*          # Unit tests
    run_tests.sh     # Small script that runs the tests
    README.md        # Documentation for 5_model component.

    Dockerfile       # Dockerfile to build the threei/kfp_model_path:latest container image
    build_image.sh   # Small script that runs docker build and docker push

    component.yaml   # model component definition in YAML format