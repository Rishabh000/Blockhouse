# Blockhouse 
## Walkthrough Video: https://drive.google.com/drive/folders/10c3F7PWIdestxnZ5qm1yMDS_8CT19aeZ?usp=sharing

## 🖥️ EC2 Instance Details

- **Instance Type**: `t3.micro`  
- **Operating System**: Ubuntu 22.04 LTS (x86_64)  
- Kafka, Zookeeper, and the backtest pipeline are deployed and tested on this instance.

---

## ⚙️ Kafka & Zookeeper Setup (via Docker Compose)

### 1. Install Docker & Docker Compose

```bash
sudo apt update && sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker
```

2. **Clone Kafka Docker Setup**
```bash
	git clone https://github.com/wurstmeister/kafka-docker.git
	cd kafka-docker
```
3. **Update docker-compose.yml**
	Ensure the following environment variables are included under the Kafka service:
```bash
	environment:
  	KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
  	KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092
  	KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
```
4. **Start Kafka + Zookeeper**
```bash
	docker-compose up -d
```
5. **Create Kafka Topic**
```bash
	docker exec -it $(docker ps -qf "ancestor=wurstmeister/kafka") \
 	kafka-topics.sh --create --topic mock_l1_stream \
  --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```
  ## Upload & Prepare Project Files

**Transfer Files to EC2**

	Use sftp to copy l1_day.csv, kafka_producer.py, backtest.py, allocator.py:
```bash
	sftp -i "your-key.pem" ubuntu@<EC2-IP>
```
**Create Python Virtual Environment**
```bash
	sudo apt install python3.10-venv  # or relevant version
	python3 -m venv venv
	source venv/bin/activate
	pip install --upgrade pip
	pip install kafka-python pandas numpy
```
**Run the Pipeline**
Start Kafka Producer:
```bash

	source venv/bin/activate
	python kafka_producer.py
```
Run Backtest:
```bash
	source venv/bin/activate
	python backtest.py
```


## Kafka + Backtest.py running on EC2
### Backtest.py
![image](https://github.com/user-attachments/assets/9e908810-1b8d-4bad-87a2-338d1af9fc85)
### Kafka
![image](https://github.com/user-attachments/assets/91df563e-4719-4338-9392-1571b90f9449)

## Output.json
![image](https://github.com/user-attachments/assets/bcc9109e-a49c-48fe-94b7-92cac1cf3665)

## Uptime 
![image](https://github.com/user-attachments/assets/248bd327-050e-4c87-ae42-ada808c83ae0)






