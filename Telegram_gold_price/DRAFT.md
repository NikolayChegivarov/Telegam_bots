# 🛠 Все команды управления ботом через Systemd
## 📋 Базовые команды
Запуск и остановка

Запустить бота  
```sudo systemctl start telegram-gold-bot.service```  
Остановить бота  
```sudo systemctl stop telegram-gold-bot.service```  
Перезапустить бота (после изменений кода)  
```sudo systemctl restart telegram-gold-bot.service```
Проверить статус бота  
```sudo systemctl status telegram-gold-bot.service```
## Автозапуск
Включить автозапуск при загрузке системы  
```sudo systemctl enable telegram-gold-bot.service```  
Выключить автозапуск  
```sudo systemctl disable telegram-gold-bot.service```  
Проверить включен ли автозапуск  
```sudo systemctl is-enabled telegram-gold-bot.service```   
## 📊 Мониторинг и логи
### Просмотр логов
Смотреть логи в реальном времени (live tail)  
```sudo journalctl -u telegram-gold-bot.service -f```  
Показать последние 50 строк логов  
```sudo journalctl -u telegram-gold-bot.service -n 50```
Показать логи с определенного времени  
```sudo journalctl -u telegram-gold-bot.service --since "2024-01-13 14:00:00"```
Показать логи за последние 2 часа  
```sudo journalctl -u telegram-gold-bot.service --since "2 hours ago"```
Показать логи за сегодня  
```sudo journalctl -u telegram-gold-bot.service --since today```
Показать логи с определенного уровня (error, warning, info)  
```sudo journalctl -u telegram-gold-bot.service -p err``` 
```sudo journalctl -u telegram-gold-bot.service -p warning```  
### Экспорт логов
Сохранить логи в файл    
```sudo journalctl -u telegram-gold-bot.service > bot_logs.txt```  
Сохранить логи за определенный период    
```sudo journalctl -u telegram-gold-bot.service --since "2024-01-13" --until "2024-01-14" > logs_13-14_jan.txt```
Показать логи в формате JSON  
```sudo journalctl -u telegram-gold-bot.service -o json```  
Показать логи с детальной информацией  
```sudo journalctl -u telegram-gold-bot.service -o verbose```
## ⚙️ Управление systemd
### Перезагрузка конфигурации
Перезагрузить конфигурацию systemd (после изменения .service файла)  
```sudo systemctl daemon-reload```
Перезагрузить только определенный сервис  
```sudo systemctl reload telegram-gold-bot.service```
Сбросить счетчики сбоев  
```sudo systemctl reset-failed telegram-gold-bot.service```
### Информация о сервисе
Показать полную информацию о сервисе  
```sudo systemctl show telegram-gold-bot.service```
Показать зависимости сервиса  
```sudo systemctl list-dependencies telegram-gold-bot.service```
Показать PID процесса  
```sudo systemctl show telegram-gold-bot.service --property=MainPID```
Показать используемую память  
```sudo systemctl show telegram-gold-bot.service --property=MemoryCurrent```
## 🚦 Управление состоянием
### Принудительные действия
Принудительно остановить (kill)  
```sudo systemctl kill telegram-gold-bot.service```    
Остановить и отключить    
```sudo systemctl mask telegram-gold-bot.service```  
Разблокировать сервис  
```sudo systemctl unmask telegram-gold-bot.service```
Перезагрузить конфигурацию и перезапустить  
```sudo systemctl daemon-reload && sudo systemctl restart telegram-gold-bot.service```
### Проверка состояния
Проверить активен ли сервис  
```sudo systemctl is-active telegram-gold-bot.service```  
Проверить работает ли сервис  
```sudo systemctl is-failed telegram-gold-bot.service```  
Показать все юниты  
```sudo systemctl list-units --type=service```  
Показать только активные сервисы      
```sudo systemctl list-units --type=service --state=active```  
Показать сервисы с ошибками  
```sudo systemctl list-units --type=service --state=failed ``` 
## 📝 Работа с конфигурацией
Просмотр конфига
Показать конфигурационный файл  
```cat /etc/systemd/system/telegram-gold-bot.service```  
Показать с подсветкой синтаксиса (если установлен bat)  
```bat /etc/systemd/system/telegram-gold-bot.service```  
Проверить синтаксис конфига  
```sudo systemd-analyze verify /etc/systemd/system/telegram-gold-bot.service```  
Редактирование конфига  
Редактировать конфиг (используйте nano, vim или другой редактор)  
```sudo nano /etc/systemd/system/telegram-gold-bot.service```  
После редактирования обязательно:  
```sudo systemctl daemon-reload```  
```sudo systemctl restart telegram-gold-bot.service```
