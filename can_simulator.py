import simpy
import random

# 재시도 큐 처리기
def retry_manager(env, retry_queue, bus_log, retry_delay=3):
    while True:
        yield env.timeout(1)
        current_time = env.now
        to_retry = [item for item in retry_queue if item[0] <= current_time]
        for item in to_retry:
            _, ecu_name, retry_count = item
            retry_queue.remove(item)

            # 재전송 시도
            if random.random() < 0.1:
                print(f"[{env.now}] 🔁 ❌ 재전송 실패 ({ecu_name})")
                bus_log.append((env.now, ecu_name, "FAIL", {"retry": True}))
            else:
                print(f"[{env.now}] 🔁 ✅ 재전송 성공 ({ecu_name})")
                bus_log.append((env.now, ecu_name, "OK", {"retry": True}))

# ECU 기본 통신
def ecu(env, name, bus_log, retry_queue, error_rate=0.1):
    while True:
        yield env.timeout(1)
        timestamp = env.now

        if random.random() < error_rate:
            print(f"[{timestamp}] ❌ {name} 전송 실패")
            bus_log.append((timestamp, name, "FAIL", {"retry": False}))
            retry_queue.append((timestamp + 3, name, 1))  # 3초 뒤에 1회 재시도
        else:
            print(f"[{timestamp}] ✅ {name} 메시지 전송 성공")
            bus_log.append((timestamp, name, "OK", {}))

# 시뮬레이터 실행
if __name__ == "__main__":
    env = simpy.Environment()
    bus_log = []
    retry_queue = []

    # ECU 3개
    env.process(ecu(env, "ECU1", bus_log, retry_queue))
    env.process(ecu(env, "ECU2", bus_log, retry_queue))
    env.process(ecu(env, "ECU3", bus_log, retry_queue))

    # 재시도 처리기
    env.process(retry_manager(env, retry_queue, bus_log))

    env.run(until=40)

    # 결과 확인
    print("\n📊 전체 로그:")
    for log in bus_log:
        print(log)

