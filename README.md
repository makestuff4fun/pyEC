# pyEC
microPython E-bike/EV computer

Introducing the pyEC, a pyBoard Compatible E-Bike Computer
The pyEC is a pyBoard compatible multipurpose board capable of talking with just about anything on your E-bike. In fact it’s more a general purpose board capable of doing a whole host of digital electronic tasks. If you are not familiar with the pyBoard, it’s a STM32 based board that runs a type of python for micro controllers, microPython.

The idea behind the pyEC is that there are a number of layers interconnected to provide just the functionality you need and none of what you don’t. The main board, or “Layer” as I’ve taken to calling them, is the main pyBoard v1.1 compatible board. It has a ton packed into a 4cm*4cm package. 50 pin header for inter-layer communications, CAN, OP Amp, Buzzer, LEDs, SD Card socket, user & reset switches and of course USB for debugging and loading on new programs. Most connectivity has been moved to other “layers”. The “Control Layer” is just that, it controls all the layers and has the MCU. Without any additional layers it can basically just blink and beep.

Layers
Control Layer – pyBoard v1.1 compatible board w/USB, SD Card, Buzzer, USR/RST Switches and an RGB LED

Serial Layer – Exposes 4  Serial ports complete with RX/TX LEDs for easy debugging and 3.3V/5V level shifters

Input Layer –  Gives 5 switch Inputs and 2 Analog inputs, all with optional voltage dividers to scale inputs

Power Layer – Power input (12V), 5V output, 2 High power & 3 Low power digitally controlled outputs

Kelly Layer – 24V Step-Up converter, DAC Outputs, digital Outputs & UART. Designed for Kelly KLS-S controllers

Battery Backup Layer – Provides LiPo charging and either 5V stable output from LiPo

IMU Layer – Provides a WIT Motion IMU through either I2C or serial. GPS input and direct IMU access ports are provided.

Test Layer – Exposes all pins from the Control Layer as well as buttons / LEDs on IO pins and Potentiometers for ADCs

Control Layer

The control layer is the beating heart of the pyEC and a board I had a lot of fun designing. It’s a 1mm 4 layer PCB with black silkscreen and gold plated contacts, because who doesn’t love black and gold? The design and pinout are compatible with pyBoard V1.1 with some minor changes. It’s firmware compatible so you can add any firmware you want without having to re-compile it. I have removed the original onboard IMU in favor of an external 9 DOF  IMU. I have also removed 1 LED giving 3 instead of 4. This allows the LED to be a single RGB LED which is compact and should give enough outputs for debugging and user messages. I’ve added a buzzer output that can be configured for onboard or external buzzer at 3.3V, 5V or 12V. This could even be used as an alarm output if you wanted. USB port, SD card, user & reset switches remain consistent with the pyBoard. There is an OP Amp to scale the 3.3V DAC output to 5V to be more compatible with E-Bike accessories like throttle inputs. This can be configured to output 3.3V as well.

Power Layer
The “Power Layer” is designed to take a wide range of input voltages, though 12V is standard, and provide 5V to the rest of the stack. High voltage is also provided to the rest of the stack. In addition to providing 5V, there are high voltage outputs for accessories like a headlight and horn. There are several lower current high voltage outputs for things like brake lights, turn signals and other accessories. All outputs are digitally controlled from the “Control Layer” and some support PWM, though I have not found this to be useful. My lights use constant current drivers with wide voltage input ranges and PWM does not dim or otherwise affect the output. It is however possible and could be useful for things like high current alarms or buzzers.


Kelly Layer

The “Kelly Layer” is designed to interface with Kelly Controls KLS controllers. This layer has a 12V to 24V boost converter so it can control the on/off of the Kelly Controller (12V is insufficient). There is also a serial port, Hi/Low speed switch, and 2 DAC outputs (throttle and regen). DAC outputs are 5V by default but could be configured to be 3.3V with a jumper on the “Control Layer”.

Serial Layer
The “Serial Layer” exposes 4 serial ports. Each interface has a configurable level shifter for 5V compatibility. The STM32 is 5V tolerant and in most cases these can be bypassed but are provided in case needed. Technically they make 5V serial communications more robust. Level shifting is based on BSS138 mosfets as seen on SparkFun. Depending on how the IMU layer is configured, one serial port could be shared by two layers. Serial outputs are configured to only provide 5V, though signals could be either 3.3V or 5V. In the future I will add a jumper so each output can be configured for 3.3V or 5V output. Currently all my Serial devices are 5V compatible so it’s not been an issue yet.


Battery Backup

The “Battery Backup Layer” provides a reliable way to prevent data loss or other corruption during the event of power loss. In my bike this could happen if the BMS shuts off due to over current or other fault condition. In this case if there is an open log file or a write in process, the SD Card could be corrupted. The default state is charging the battery and if power is lost, the MCU can activate the 5V boost converter. The “Control Layer” has a 12V detect and can detect a power loss. There are also a number of capacitors connected to 3.3 volts to give the MCU enough time to detect the power loss and react by activating the boost converter. The charge and boost circuits are mutually exclusive preventing unwanted operation. Currently only single cell lipo’s are supported. 18650 cells or pouch cells are both OK, though max voltage is set at 4.2V.

Input Layer
The “Input Layer” has 5 digital inputs and 2 ADC inputs. Digital inputs have configurable voltage dividers and optional de-bouncing capacitor. ADC inputs also have voltage dividers. ADC ports also provide 5V to be compatible with standard E-bike throttles or potentiometers. ADC could also be configured as digital inputs if needed. The idea for having two ADC inputs is to connect to the E-bike throttle and regen braking inputs for logging or so they can be scaled or have any type of throttle curve applied.


Test Layer

The “Test Layer” provides pinouts for all header pins. This gives a way to prototype new layers or monitor specific pins for debugging. There are also pots connected to the ADCs, LEDs connected to the DACs, buttons connected to the switch inputs and LEDs for “Power Layer” outputs. It is my attempt to help debugging software/hardware problems. It can also be used to provide stable input values during software development.

IMU Layer
The “IMU Layer” provides a WIT Motion JY901B 10 axis IMU. This is a great little unit and can also provide info from a connected GPS. This offloads the GPS string parsing from the control layer but still allows GPS information to be used. There are several digital/PWM outputs that can be configured as well. There is a connection for direct connection to the IMU for configuration, a reset jumper, GPS port and IMU io port. This layer by default uses serial to communicate with the IMU but can be configured to use I2C as well.

more information can be found at http://makestuff4.fun/pyec/

