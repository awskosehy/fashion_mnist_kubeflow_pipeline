sh 0_kfp/build_image.sh;
cd 1_fashion_mnist/;
sh build_image.sh;
cd ../2_katib/;
sh build_image.sh;
cd ../3_tensorboard/;
sh build_image.sh;
cd ../4_model_path/;
sh build_image.sh;
cd ..
