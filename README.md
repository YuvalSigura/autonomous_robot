# autonomous_robot
autonomous_robot/
├── README.md
├── LICENSE
├── requirements.txt
├── setup.py
├── config/
│   └── config.yaml
├── data/
│   ├── datasets/
│   │   ├── training/
│   │   └── validation/
│   ├── models/
│   │   ├── model_best.pth
│   │   └── model_final.pth
│   └── logs/
│       └── training_logs.txt
├── docs/
│   ├── hardware_schematics/
│   │   ├── wiring_diagram.png
│   │   └── wiring_diagram_source.fzz
│   ├── software_architecture.md
│   └── user_manual.md
├── logs/
│   ├── runtime_logs.txt
│   └── error_logs.txt
├── scripts/
│   ├── calibrate_camera.py
│   ├── collect_data.py
│   ├── preprocess_data.py
│   └── train_model.py
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── camera/
│   │   ├── __init__.py
│   │   └── camera_module.py
│   ├── control/
│   │   ├── __init__.py
│   │   ├── control_module.py
│   │   └── pid_controller.py
│   ├── hardware_interface/
│   │   ├── __init__.py
│   │   ├── gpio_interface.py
│   │   └── motor_driver.py
│   ├── perception/
│   │   ├── __init__.py
│   │   ├── ai_model.py
│   │   ├── lane_detection.py
│   │   └── object_detection.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       ├── config_loader.py
│       └── image_processing.py
└── venv/
    └── [Python virtual environment files]



Introduction
This project involves building an autonomous robot using the Jetson Orin Nano Developer Kit 8GB, integrating vision AI capabilities with motor control to achieve autonomous driving. The robot utilizes:

Vision AI using a USB camera (Logitech C270)
Motor Control using 2 L298N motor drivers
Power Management via a DC-DC converter and batteries
This README provides a comprehensive step-by-step guide to set up, configure, and run the project, including the updated project structure and code snippets.

