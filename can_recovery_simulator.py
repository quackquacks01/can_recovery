import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 시뮬레이션 설정
SIM_DURATION = 40
ERROR_RATE = 0.1
RETRY_DELAY = 3

# 로깅 변수
bus_log = []
retry_queue = []

# 재전송 처리 로직
def retry_manager(env, retry_queue, bus_log):
    while True:
        yield env.timeout(1)
        current_time = env.now
        to_retry = [item for item in retry_queue if item[0] <= current_time]
        for item in to_retry:
            _, ecu_name, retry_count = item
            retry_queue.remove(item)
            if random.random() < ERROR_RATE:
                print(f"[{env.now}] 🔁 ❌ 재전송 실패 ({ecu_name})")
                bus_log.append((env.now, ecu_name, "FAIL", {"retry": True}))
            else:
                print(f"[{env.now}] 🔁 ✅ 재전송 성공 ({ecu_name})")
                bus_log.append((env.now, ecu_name, "OK", {"retry": True}))

# ECU 전송 시를리오

def ecu(env, name, bus_log, retry_queue):
    while True:
        yield env.timeout(1)
        timestamp = env.now
        if random.random() < ERROR_RATE:
            print(f"[{timestamp}] ❌ {name} 전송 실패")
            bus_log.append((timestamp, name, "FAIL", {"retry": False}))
            retry_queue.append((timestamp + RETRY_DELAY, name, 1))
        else:
            print(f"[{timestamp}] ✅ {name} 메시지 전송 성공")
            bus_log.append((timestamp, name, "OK", {}))

# 시를리오 실행
def run_simulation():
    env = simpy.Environment()
    env.process(ecu(env, "ECU1", bus_log, retry_queue))
    env.process(ecu(env, "ECU2", bus_log, retry_queue))
    env.process(ecu(env, "ECU3", bus_log, retry_queue))
    env.process(retry_manager(env, retry_queue, bus_log))
    env.run(until=SIM_DURATION)

    df = pd.DataFrame(bus_log, columns=["time", "ecu", "status", "meta"])
    df["retry"] = df["meta"].apply(lambda x: x.get("retry", False))
    df.drop("meta", axis=1, inplace=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    df.to_csv(f"can_sim_result_{timestamp}.csv", index=False)

    print("\n\u2705 [결과 정보]")
    total = len(df)
    success = df[df["status"] == "OK"]
    fail = df[df["status"] == "FAIL"]
    retry_success = df[(df["status"] == "OK") & (df["retry"] == True)]
    retry_attempts = df[df["retry"] == True]

    print(f"- 전체 메시지: {total} 개")
    print(f"- 전송 성공률: {len(success)/total*100:.2f}%")
    print(f"- 재전송 성공률: {len(retry_success)}/{len(retry_attempts)} = {len(retry_success)/len(retry_attempts)*100:.2f}%" if len(retry_attempts) > 0 else "- 재전송 없음")

    df.groupby(["time", "status"]).size().unstack(fill_value=0).plot(kind="bar", stacked=True)
    plt.title("Transmission Success/Failure Count by Time")
    plt.xlabel("time")
    plt.ylabel("message")
    plt.tight_layout()
    plt.savefig(f"can_sim_plot_{timestamp}.png")
    plt.close()

if __name__ == "__main__":
    run_simulation()
