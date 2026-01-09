"""
테스트 데이터 삭제 스크립트
실험 데이터에서 테스트용으로 생성된 데이터를 삭제합니다.
"""
import requests
import json
from typing import List

# API 설정
BASE_URL = "http://localhost:8000/api/research"


def list_all_rooms():
    """모든 room 목록 조회"""
    response = requests.get(
        f"{BASE_URL}/experiments/export",
        params={"started_only": False, "with_consent_only": False, "skip": 0, "limit": 1000}
    )
    data = response.json()
    
    print(f"\n총 {data['total_count']}개의 room이 있습니다.")
    print("\n=== Room 목록 ===")
    for room in data["rooms"]:
        print(f"ID: {room['room_id']}, 코드: {room['room_code']}, 제목: {room['title']}, "
              f"시작됨: {room['is_started']}, 참가자: {len(room['participants'])}")
    
    return data["rooms"]


def delete_rooms(room_ids: List[int], delete_voice_files: bool = False):
    """선택한 room들 삭제"""
    if not room_ids:
        print("삭제할 room이 없습니다.")
        return
    
    print(f"\n삭제할 room IDs: {room_ids}")
    confirm = input("정말 삭제하시겠습니까? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("삭제가 취소되었습니다.")
        return
    
    response = requests.post(
        f"{BASE_URL}/experiments/cleanup",
        json={
            "room_ids": room_ids,
            "user_ids": [],
            "delete_voice_files": delete_voice_files
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ 삭제 완료:")
        print(f"  - 삭제된 rooms: {result['deleted_rooms']}")
        print(f"  - 삭제된 users: {result['deleted_users']}")
        print(f"  - 삭제된 voice recordings: {result['deleted_voice_recordings']}")
        print(f"  - {result['message']}")
    else:
        print(f"\n❌ 삭제 실패: {response.status_code}")
        print(response.text)


def delete_by_criteria():
    """조건에 따라 삭제할 room 선택"""
    rooms = list_all_rooms()
    
    print("\n삭제 기준을 선택하세요:")
    print("1. 시작되지 않은 room 삭제")
    print("2. 참가자가 없는 room 삭제")
    print("3. 특정 room ID 직접 입력")
    print("4. 모든 테스트 room 삭제 (제목에 'test' 또는 '테스트' 포함)")
    print("5. 취소")
    
    choice = input("\n선택 (1-5): ")
    
    room_ids_to_delete = []
    
    if choice == "1":
        # 시작되지 않은 room
        room_ids_to_delete = [r["room_id"] for r in rooms if not r["is_started"]]
        print(f"\n시작되지 않은 room {len(room_ids_to_delete)}개를 찾았습니다.")
        
    elif choice == "2":
        # 참가자가 없는 room
        room_ids_to_delete = [r["room_id"] for r in rooms if len(r["participants"]) == 0]
        print(f"\n참가자가 없는 room {len(room_ids_to_delete)}개를 찾았습니다.")
        
    elif choice == "3":
        # 직접 입력
        ids_str = input("\n삭제할 room ID를 쉼표로 구분해서 입력하세요 (예: 1,2,3): ")
        room_ids_to_delete = [int(id.strip()) for id in ids_str.split(",") if id.strip()]
        
    elif choice == "4":
        # 테스트 room
        room_ids_to_delete = [
            r["room_id"] for r in rooms 
            if "test" in r["title"].lower() or "테스트" in r["title"].lower()
        ]
        print(f"\n테스트 room {len(room_ids_to_delete)}개를 찾았습니다.")
        
    elif choice == "5":
        print("취소되었습니다.")
        return
    
    else:
        print("잘못된 선택입니다.")
        return
    
    if room_ids_to_delete:
        # 음성 파일도 삭제할지 선택
        delete_voice = input("\n음성 파일도 삭제하시겠습니까? (yes/no, 기본: no): ")
        delete_voice_files = delete_voice.lower() == 'yes'
        
        delete_rooms(room_ids_to_delete, delete_voice_files)
    else:
        print("\n삭제할 room이 없습니다.")


def show_statistics():
    """데이터 통계 보기"""
    response = requests.get(f"{BASE_URL}/experiments/summary")
    
    if response.status_code == 200:
        stats = response.json()
        print("\n=== 데이터 통계 ===")
        print(f"총 사용자 수: {stats['total_users']}")
        print(f"동의한 사용자 수: {stats['users_with_full_consent']}")
        print(f"총 room 수: {stats['total_rooms']}")
        print(f"시작된 room 수: {stats['total_started_rooms']}")
        print(f"총 음성 녹음 수: {stats['total_voice_recordings']}")
        print(f"총 라운드 선택 수: {stats['total_round_choices']}")
        print(f"총 합의 선택 수: {stats['total_consensus_choices']}")
    else:
        print(f"통계 조회 실패: {response.status_code}")


def main():
    """메인 함수"""
    print("=" * 60)
    print("테스트 데이터 삭제 스크립트")
    print("=" * 60)
    
    while True:
        print("\n메뉴:")
        print("1. 데이터 통계 보기")
        print("2. 모든 room 목록 보기")
        print("3. 조건에 따라 room 삭제")
        print("4. 종료")
        
        choice = input("\n선택 (1-4): ")
        
        if choice == "1":
            show_statistics()
        elif choice == "2":
            list_all_rooms()
        elif choice == "3":
            delete_by_criteria()
        elif choice == "4":
            print("\n프로그램을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
