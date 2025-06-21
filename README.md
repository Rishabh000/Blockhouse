# Blockhouse Work Trial Repo

This repository consists of the following components:

1. **Benchmarks** – Code for TWAP and VWAP strategies.  
2. **Cost Calculations** – Code for calculating various costs within the rewards component.  
3. **Datasets** – Example datasets that can be used for this process.  

---

## Notes

- You are encouraged to modify or extend the cost components code if needed.
- Feel free to use any additional data or implement other logic as necessary.

---

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
```yaml
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



