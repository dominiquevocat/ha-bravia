# ha-bravia
##Bravia TV support for home-assistant.io

place it in .../site-packages/homeassistant/components/media_player

add something like

media_player 3:
  platform: bravia

to your configuration.yaml

Works kinda. Needs work still.

###New in version 0.2:
 set media :-)
 still not taking the config from the config.yaml - set ip and mac address in the source :-(

####Define your media player:
media_player 3:
```
  platform: bravia
  host: 192.168.0.12
  name: MyBraviaTV
```
 
####You could do a list of channels like this:
```
input_select:
  braviachannel:
    name: braviachannel
    options:
      - 1 SRF 1 HD
      - 2 SRF zwei HD
      - 3 SRF info HD
      (...)
    icon: mdi:television-guide
    initial: 1 SRF 1 HD
```

####Add some automation like this:
```
automation:
  alias: TV channel
  trigger:
    platform: state
    entity_id: input_select.braviachannel
  action:
    service: media_player.select_source
    data_template:
      entity_id: media_player.mybraviatv
      source: "{{ states.input_select.braviachannel.state }}"
```

####Group it all like this:
```
group:
  Livingroom:
    name: Livingroom
    entities:
      - light.livingcolors_1
      - light.livingcolors_2
      - input_select.braviachannel
      - media_player.mybraviatv
```
