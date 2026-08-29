import requests
import json

def check_fssp_api(last_name, first_name, birth_date, middle_name=None):
    """
    Проверка наличия исполнительных производств через API ФССП.
    """
    url = "https://api.fssp.gov.ru/api/v1/ip/search"
    
    params = {
        "region": "all",
        "type": "person",
        "first_name": first_name,
        "last_name": last_name,
        "birth_date": birth_date
    }
    
    if middle_name:
        params["middle_name"] = middle_name
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print(f"Проверяем: {last_name} {first_name} {middle_name or ''} {birth_date}")
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("response", {}).get("items"):
                total_debt = 0
                productions = []
                
                for item in data["response"]["items"]:
                    debt = float(item.get("amount", 0))
                    total_debt += debt
                    productions.append({
                        "number": item.get("number", ""),
                        "amount": debt,
                        "status": item.get("status", ""),
                        "department": item.get("department", {}).get("name", ""),
                        "date": item.get("date", "")
                    })
                
                return {
                    "success": True,
                    "has_debts": True,
                    "total_debt": total_debt,
                    "count": len(productions),
                    "productions": productions,
                    "message": f"Найдено {len(productions)} исполнительных производств на сумму {total_debt:,.2f} руб."
                }
            else:
                return {
                    "success": True,
                    "has_debts": False,
                    "message": "Исполнительных производств не найдено"
                }
        else:
            return {
                "success": False,
                "error": f"Ошибка API: {response.status_code}",
                "message": f"Сервис временно недоступен (код {response.status_code})"
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Timeout",
            "message": "Превышено время ожидания ответа от сервера ФССП"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Ошибка: {str(e)}"
        }

if __name__ == "__main__":
    # Пример использования
    result = check_fssp_api(
        last_name="Иванов",
        first_name="Иван",
        birth_date="01.01.1980",
        middle_name="Иванович"
    )
    
    print("\n" + "="*50)
    print("РЕЗУЛЬТАТ ПРОВЕРКИ:")
    print("="*50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
