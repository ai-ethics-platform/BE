"""
실험 데이터 export 예제 스크립트
연구진이 데이터를 다양한 형식으로 export하는 예제입니다.
"""
import requests
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any


BASE_URL = "http://localhost:8000/api/research"
OUTPUT_DIR = "exported_data"


def export_all_data_json():
    """모든 실험 데이터를 JSON 파일로 export"""
    print("📥 모든 실험 데이터를 가져오는 중...")
    
    all_rooms = []
    skip = 0
    limit = 100
    
    while True:
        response = requests.get(
            f"{BASE_URL}/experiments/export",
            params={
                "started_only": True,
                "with_consent_only": True,
                "skip": skip,
                "limit": limit
            }
        )
        
        if response.status_code != 200:
            print(f"❌ 데이터 가져오기 실패: {response.status_code}")
            return None
        
        data = response.json()
        all_rooms.extend(data["rooms"])
        
        print(f"  - {len(data['rooms'])}개 room 가져옴 (전체: {data['total_count']})")
        
        if len(data["rooms"]) < limit:
            break
        skip += limit
    
    # JSON 파일로 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/experiment_data_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_rooms, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ {len(all_rooms)}개의 room 데이터를 {filename}에 저장했습니다.")
    return all_rooms


def export_choices_csv(rooms_data: List[Dict[str, Any]]):
    """선택 데이터를 CSV 파일로 export"""
    print("\n📊 선택 데이터를 CSV로 변환 중...")
    
    rows = []
    
    for room in rooms_data:
        for participant in room["participants"]:
            for choice in participant["round_choices"]:
                row = {
                    "room_id": room["room_id"],
                    "room_code": room["room_code"],
                    "topic": room["topic"],
                    "ai_type": room["ai_type"],
                    "ai_name": room["ai_name"],
                    "participant_id": participant["participant_id"],
                    "nickname": participant["nickname"],
                    "role_id": participant["role_id"],
                    "is_host": participant["is_host"],
                    "round_number": choice["round_number"],
                    "choice": choice["choice"],
                    "confidence": choice["confidence"],
                    "subtopic": choice["subtopic"],
                    "choice_created_at": choice["created_at"]
                }
                
                # 사용자 정보 추가
                if participant["user_data"]:
                    user = participant["user_data"]
                    row.update({
                        "user_id": user["user_id"],
                        "username": user["username"],
                        "gender": user["gender"],
                        "birthdate": user["birthdate"],
                        "education_level": user["education_level"],
                        "major": user["major"]
                    })
                
                rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/choices_data_{timestamp}.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    
    print(f"✅ {len(df)}개의 선택 데이터를 {filename}에 저장했습니다.")
    
    # 기본 통계 출력
    print("\n📈 기본 통계:")
    print(f"  - 총 참가자 수: {df['participant_id'].nunique()}")
    print(f"  - 총 라운드 수: {df['round_number'].max()}")
    print(f"  - 평균 확신도: {df['confidence'].mean():.2f}")
    
    return df


def export_consensus_csv(rooms_data: List[Dict[str, Any]]):
    """합의 선택 데이터를 CSV 파일로 export"""
    print("\n📊 합의 선택 데이터를 CSV로 변환 중...")
    
    rows = []
    
    for room in rooms_data:
        for consensus in room["consensus_choices"]:
            row = {
                "room_id": room["room_id"],
                "room_code": room["room_code"],
                "topic": room["topic"],
                "ai_type": room["ai_type"],
                "round_number": consensus["round_number"],
                "choice": consensus["choice"],
                "confidence": consensus["confidence"],
                "subtopic": consensus["subtopic"],
                "created_at": consensus["created_at"]
            }
            rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/consensus_data_{timestamp}.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    
    print(f"✅ {len(df)}개의 합의 선택 데이터를 {filename}에 저장했습니다.")
    
    return df


def export_voice_recordings_csv(rooms_data: List[Dict[str, Any]]):
    """음성 녹음 데이터를 CSV 파일로 export"""
    print("\n🎤 음성 녹음 데이터를 CSV로 변환 중...")
    
    rows = []
    
    for room in rooms_data:
        for voice_session in room["voice_sessions"]:
            for recording in voice_session["recordings"]:
                row = {
                    "room_id": room["room_id"],
                    "room_code": room["room_code"],
                    "topic": room["topic"],
                    "session_id": voice_session["session_id"],
                    "recording_id": recording["id"],
                    "user_id": recording["user_id"],
                    "guest_id": recording["guest_id"],
                    "file_path": recording["file_path"],
                    "file_size_bytes": recording["file_size"],
                    "duration_seconds": recording["duration"],
                    "is_processed": recording["is_processed"],
                    "created_at": recording["created_at"]
                }
                rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/voice_recordings_{timestamp}.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    
    print(f"✅ {len(df)}개의 음성 녹음 데이터를 {filename}에 저장했습니다.")
    
    if len(df) > 0:
        print(f"\n📈 음성 녹음 통계:")
        print(f"  - 총 녹음 수: {len(df)}")
        print(f"  - 총 녹음 시간: {df['duration_seconds'].sum() / 60:.2f}분")
        print(f"  - 평균 녹음 시간: {df['duration_seconds'].mean():.2f}초")
    
    return df


def export_users_csv():
    """사용자 정보를 CSV 파일로 export"""
    print("\n👥 사용자 정보를 CSV로 변환 중...")
    
    # 사용자 정보는 rooms에서 추출
    response = requests.get(
        f"{BASE_URL}/experiments/export",
        params={"started_only": False, "with_consent_only": False, "skip": 0, "limit": 1000}
    )
    
    if response.status_code != 200:
        print(f"❌ 데이터 가져오기 실패: {response.status_code}")
        return None
    
    data = response.json()
    rooms = data["rooms"]
    
    # 사용자 정보 중복 제거
    users_dict = {}
    
    for room in rooms:
        for participant in room["participants"]:
            if participant["user_data"]:
                user = participant["user_data"]
                user_id = user["user_id"]
                if user_id not in users_dict:
                    users_dict[user_id] = {
                        "user_id": user_id,
                        "username": user["username"],
                        "email": user["email"],
                        "birthdate": user["birthdate"],
                        "gender": user["gender"],
                        "education_level": user["education_level"],
                        "major": user["major"],
                        "data_consent": user["data_consent"],
                        "voice_consent": user["voice_consent"],
                        "created_at": user["created_at"]
                    }
    
    df = pd.DataFrame(list(users_dict.values()))
    
    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/users_data_{timestamp}.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    
    print(f"✅ {len(df)}명의 사용자 데이터를 {filename}에 저장했습니다.")
    
    return df


def get_choice_analysis():
    """선택 데이터 분석 결과 가져오기"""
    print("\n📊 선택 데이터 분석 중...")
    
    response = requests.get(f"{BASE_URL}/experiments/choices/analysis")
    
    if response.status_code != 200:
        print(f"❌ 분석 실패: {response.status_code}")
        return None
    
    analysis = response.json()
    
    # 라운드별 선택 분석
    print("\n=== 라운드별 선택 분석 ===")
    round_df = pd.DataFrame(analysis["round_choices"])
    print(round_df.to_string(index=False))
    
    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    round_filename = f"{OUTPUT_DIR}/round_analysis_{timestamp}.csv"
    round_df.to_csv(round_filename, index=False, encoding="utf-8-sig")
    print(f"\n✅ 라운드 분석 결과를 {round_filename}에 저장했습니다.")
    
    # 역할별 선택 분석
    print("\n=== 역할별 선택 분석 ===")
    role_df = pd.DataFrame(analysis["role_choices"])
    print(role_df.to_string(index=False))
    
    role_filename = f"{OUTPUT_DIR}/role_analysis_{timestamp}.csv"
    role_df.to_csv(role_filename, index=False, encoding="utf-8-sig")
    print(f"\n✅ 역할 분석 결과를 {role_filename}에 저장했습니다.")
    
    return analysis


def main():
    """메인 함수"""
    print("=" * 70)
    print("실험 데이터 Export 스크립트")
    print("=" * 70)
    
    # 출력 디렉토리 생성
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. JSON으로 전체 데이터 export
    rooms_data = export_all_data_json()
    
    if rooms_data:
        # 2. 선택 데이터 CSV export
        export_choices_csv(rooms_data)
        
        # 3. 합의 선택 데이터 CSV export
        export_consensus_csv(rooms_data)
        
        # 4. 음성 녹음 데이터 CSV export
        export_voice_recordings_csv(rooms_data)
    
    # 5. 사용자 데이터 CSV export
    export_users_csv()
    
    # 6. 선택 분석 결과
    get_choice_analysis()
    
    print("\n" + "=" * 70)
    print("✅ 모든 데이터 export가 완료되었습니다!")
    print(f"📁 출력 디렉토리: {OUTPUT_DIR}/")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
