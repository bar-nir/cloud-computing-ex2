This guide will help you set up the project and run it on an EC2 instance.

1. clone the project and install requirements

```bash
git clone git@github.com:bar-nir/cloud-computing-ex1.git
```

```bash
cd cloud-computing-ex1
```

```bash
pip3 install -r requirements.txt
```

2. Deploy the server to EC2 with the following command

```bash
python3 setup.py
```

3. Tear down all resources when finishing

```bash
python3 teardown.py
```
