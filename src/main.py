from monitoring_app import MonitoringApp


# TODO 서버는 프롬프트 화면이 나오지 않게 하고, 중복 실행 방지 로직 추가
if __name__ == '__main__':
    server = MonitoringApp()
    server.run()
