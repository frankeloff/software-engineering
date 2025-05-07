workspace {
    name "Бюджетирование"

    !identifiers hierarchical

    model {
        properties { 
            structurizr.groupSeparator "/"
        }

        user = person "Пользователь" {
            description "Управляет своим бюджетом"
            tags "user"
        }

        budgeting_system = softwareSystem "Система Бюджетирования" {
            description "Позволяет управлять доходами и расходами"
            tags "system"

            user_service = container "User Service" {
                description "Управляет пользователями"
                technology "Python/Litestar"
                tags "service"
            } 

            budget_service = container "Budget Service" {
                description "Управляет доходами и расходами"
                technology "Python/Litestar"
                tags "service"
            } 

            database = container "Database" {
                description "Хранит данные пользователей, доходов и расходов"
                technology "PostgreSQL"
                tags "database"
            }

            mongo = container "Mongo" {
                description "Хранит данные доходов и расходов"
                technology "MongoDB"
                tags "database"
            }


            redis = container "Redis" {
                description "Хранит сессии пользователей и кэш"
                technology "Redis"
                tags "cache"
            }

            report_service = container "Report Service" {
                description "Генерирует отчеты"
                technology "Python/Litestar"
                tags "service"
            }

            user -> user_service "Регистрация и вход"
            user_service -> database "Сохранение и получение данных"
            user_service -> redis "Сохранение сессии (JWT)/Получение кэша"

            user -> budget_service "Управление бюджетом"
            budget_service -> redis "Получение сессии"
            budget_service -> mongo "Сохранение и получение бюджета"
            budget_service -> user "Возвращает актуальный баланс"

            user -> budget_service "Запрос на создание отчета"
            budget_service -> report_service "Запрос на создание отчета"
            report_service -> mongo "Извлечение данных для отчета"
            report_service -> budget_service "Отчет готов"
            budget_service -> user "Сообщение о готовности отчета"
        }

        user -> budgeting_system "Использует систему для управления бюджетом"
    }

    views {
        themes default

        properties {
            structurizr.tooltips true
        }

        systemContext budgeting_system {
            autoLayout lr 1000 1000
            include *
        }

        container budgeting_system {
            autoLayout tb 500 250
            include *
        }

        dynamic budgeting_system "Case1" "Создание нового пользователя" {
            autoLayout
            user -> budgeting_system.user_service "Создание пользователя (POST /user)"
            budgeting_system.user_service -> budgeting_system.database "Сохранение данных о пользователе"
            budgeting_system.user_service -> budgeting_system.redis "Кэширование пользователя"
            budgeting_system.user_service -> user "Возвращает подтверждение регистрации"
        }

        dynamic budgeting_system "Case2" "Авторизация пользователя" {
            autoLayout
            user -> budgeting_system.user_service "Авторизация (POST /auth)"
            budgeting_system.user_service -> budgeting_system.database "Проверка учетных данных"
            budgeting_system.user_service -> budgeting_system.redis "Сохранение сессии"
            budgeting_system.user_service -> user "Возвращает токен авторизации"
        }

        dynamic budgeting_system "Case3" "Создание планируемого дохода" {
            autoLayout tb 1000 100
            user -> budgeting_system.user_service "Авторизация (POST /auth)"
            budgeting_system.user_service -> user "Возвращает токен авторизации"
            user -> budgeting_system.budget_service "Создание дохода (POST /income)"
            budgeting_system.budget_service -> budgeting_system.redis "Проверка наличия сессии"
            budgeting_system.budget_service -> budgeting_system.mongo "Сохранение дохода"
            budgeting_system.budget_service -> user "Возвращает подтверждение операции"
        }

        dynamic budgeting_system "Case4" "Создание планируемого расхода" {
            autoLayout tb 1000 100
            user -> budgeting_system.user_service "Авторизация (POST /auth)"
            budgeting_system.user_service -> user "Возвращает токен авторизации"
            user -> budgeting_system.budget_service "Создание расхода (POST /expense)"
            budgeting_system.budget_service -> budgeting_system.redis "Проверка наличия сессии"
            budgeting_system.budget_service -> budgeting_system.mongo "Сохранение расхода"
            budgeting_system.budget_service -> user "Возвращает подтверждение операции"
        }

        dynamic budgeting_system "Case5" "Получение перечня планируемых доходов" {
            autoLayout tb 1000 100
            user -> budgeting_system.user_service "Авторизация (POST /auth)"
            budgeting_system.user_service -> user "Возвращает токен авторизации"
            user -> budgeting_system.budget_service "Запрос списка доходов (GET /income)"
            budgeting_system.budget_service -> budgeting_system.redis "Проверка наличия сессии"
            budgeting_system.budget_service -> budgeting_system.mongo "Извлечение данных о доходах"
            budgeting_system.budget_service -> user "Передача списка доходов"
        }

        dynamic budgeting_system "Case6" "Получение перечня планируемых расходов" {
            autoLayout tb 1000 100
            user -> budgeting_system.user_service "Авторизация (POST /auth)"
            budgeting_system.user_service -> user "Возвращает токен авторизации"
            user -> budgeting_system.budget_service "Запрос списка расходов (GET /expense)"
            budgeting_system.budget_service -> budgeting_system.redis "Проверка наличия сессии"
            budgeting_system.budget_service -> budgeting_system.mongo "Извлечение данных о расходах"
            budgeting_system.budget_service -> user "Передача списка расходов"
        }

        dynamic budgeting_system "Case7" "Запрос на генерацию отчета о динамике бюджета за период" {
            autoLayout
            user -> budgeting_system.budget_service "Запрос на создание отчета (POST /report)"
            budgeting_system.budget_service -> budgeting_system.redis "Проверка наличия сессии"
            budgeting_system.budget_service -> budgeting_system.report_service "Генерация отчета"
            budgeting_system.report_service -> budgeting_system.mongo "Извлечение данных для отчета"
            budgeting_system.budget_service -> user "Сообщение о начале генерации отчета"
        }

        dynamic budgeting_system "Case8" "Уведомление о готовности отчета" {
            autoLayout
            budgeting_system.budget_service -> user "Уведомление о готовности отчета"
        }

        styles {
            element "database" {
                shape cylinder
                background #f4b183
                color #000000
            }
            
            element "service" {
                shape roundedBox
                background #8eaadb
                color #000000
            }
            
            element "system" {
                shape box
                background #d5a6bd
                color #000000
            }
            
            element "user" {
                shape person
                background #ffe599
                color #000000
            }
        }
    }
}
