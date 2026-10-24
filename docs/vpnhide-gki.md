# VPNHide built-in · GKI Android 14 / Linux 6.1

Сборка автоматически выбирает последний успешный `CI` (`ci.yml`) ветки
`main` проекта [okhsunrog/vpnhide](https://github.com/okhsunrog/vpnhide/actions/workflows/ci.yml).
Используется точный SHA этого запуска, без постоянной привязки к версии.
При ошибке API или несовместимости исходников сборка останавливается.

Штатный upstream-интегратор создаёт патч для фактических исходников нашего
ядра после остальных изменений. Патч добавляет Kbuild/Kconfig, драйвер и
прямые вызовы из сетевых/VFS участков ядра. В обоих образах включены
`CONFIG_VPNHIDE=y` и `CONFIG_VPNHIDE_FS_HIDING=y`. Отдельный `.ko` не нужен.
Патч, отчёты интегратора, лицензия и SHA upstream входят в AnyKernel3 ZIP.

Для выбора приложений используется приложение VPNHide и соответствующий
upstream **built-in companion** (активатор настроек, без `.ko`). Они доступны
в Artifacts указанного в релизе upstream CI. Без переданной конфигурации
встроенные хуки не скрывают интерфейсы. Не устанавливайте одновременно
LKM/KPM backend вместо built-in companion.

Подробности: [upstream built-in backend](https://github.com/okhsunrog/vpnhide/blob/main/builtin/README.md).
CI проверяет применение патча, компиляцию и наличие backend в обоих образах;
работу на устройстве необходимо проверить отдельно с активным VPN и выбранными приложениями.
