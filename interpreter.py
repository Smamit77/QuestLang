import re
import sys

class GameParser:
    def __init__(self, filename):
        self.filename = filename
        self.player = {}
        self.items = {}
        self.enemies = {}
        self.rooms = {}
        self.parse_file()

    def parse_file(self):
        try:
            with open(self.filename, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: Could not find '{self.filename}'. Make sure it's in the same folder!")
            sys.exit(1)

        # Remove comments
        content = re.sub(r'#.*', '', content)

        # Parse blocks like: type name { ... } or type { ... }
        blocks = re.findall(r'(\w+)(?:\s+(\w+))?\s*\{([^}]*)\}', content)

        for block_type, name, body in blocks:
            block_type = block_type.strip()
            name = name.strip() if name else None
            body = body.strip()

            if block_type == 'player':
                self.parse_player(body)
            elif block_type == 'item':
                self.parse_item(name, body)
            elif block_type == 'enemy':
                self.parse_enemy(name, body)
            elif block_type == 'room':
                self.parse_room(name, body)

    def parse_player(self, body):
        for line in body.split('\n'):
            line = line.strip()
            if not line: continue
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                key, val = parts
                if key in ['base_hp', 'base_attack']:
                    val = int(val)
                self.player[key] = val

    def parse_item(self, name, body):
        item_data = {}
        for line in body.split('\n'):
            line = line.strip()
            if not line: continue
            match = re.match(r'(\w+)\s+(?:"([^"]+)"|(\S+))', line)
            if match:
                key, val_str, val_unquoted = match.groups()
                val = val_str if val_str is not None else val_unquoted
                if key == 'attack_bonus':
                    val = int(val)
                item_data[key] = val
        self.items[name] = item_data

    def parse_enemy(self, name, body):
        enemy_data = {}
        for line in body.split('\n'):
            line = line.strip()
            if not line: continue
            match = re.match(r'(\w+)\s+(?:"([^"]+)"|(\S+))', line)
            if match:
                key, val_str, val_unquoted = match.groups()
                val = val_str if val_str is not None else val_unquoted
                if key in ['hp', 'attack', 'defense']:
                    val = int(val)
                enemy_data[key] = val
        self.enemies[name] = enemy_data

    def parse_room(self, name, body):
        room_data = {
            'title': '',
            'desc': '',
            'items': [],
            'enemy': None,
            'exits': {}
        }
        for line in body.split('\n'):
            line = line.strip()
            if not line: continue
            
            if line.startswith('title '):
                match = re.match(r'title\s+"([^"]+)"', line)
                if match: room_data['title'] = match.group(1)
            elif line.startswith('desc '):
                match = re.match(r'desc\s+"([^"]+)"', line)
                if match: room_data['desc'] = match.group(1)
            elif line.startswith('item '):
                item_name = line.split(maxsplit=1)[1]
                room_data['items'].append(item_name)
            elif line.startswith('enemy '):
                enemy_name = line.split(maxsplit=1)[1]
                room_data['enemy'] = enemy_name
            elif line.startswith('go '):
                match = re.match(r'go\s+(\w+)\s*->\s*(\w+)(?:\s+\[requires\s+([^\]]+)\])?', line)
                if match:
                    direction, target, requirement = match.groups()
                    room_data['exits'][direction] = {
                        'target': target,
                        'requires': requirement
                    }
        self.rooms[name] = room_data

class GameEngine:
    def __init__(self, ql_file):
        parser = GameParser(ql_file)
        self.player_stats = parser.player
        self.items_db = parser.items
        self.enemies_db = parser.enemies
        self.rooms = parser.rooms
        
        self.current_room = self.player_stats.get('start_room', 'entrance')
        self.inventory = []
        self.hp = self.player_stats.get('base_hp', 100)
        self.flags = set()

    def run_tutorial(self):
        print("\n--- 📜 ADVENTURER'S BRIEFING ---")
        print("Welcome to QuestLang! To survive The Crypt of Echoes, remember these core rules:")
        print("  • Exploration: Type 'look' to see surroundings, or use directions ('n', 's', 'e', 'w').")
        print("  • Items: Type 'take [item]' to pick things up, and 'examine [item]' to inspect them.")
        print("  • Combat: Type 'attack' when an enemy blocks your path.")
        input("\n[Press Enter to step past the heavy iron gates and begin...]\n")

    def start(self):
        print("=== THE CRYPT OF ECHOES (Powered by QuestLang v2.0) ===")
        self.run_tutorial()
        self.look_around()

        while True:
            print("\n--- [Quick Bar: look | inventory | stats | n/s/e/w | take [item] | examine [item] | attack | help | quit] ---")
            command = input("> ").strip().lower()
            if not command:
                continue

            shortcuts = {"n": "go north", "s": "go south", "e": "go east", "w": "go west"}
            command = shortcuts.get(command, command)

            if command == "quit":
                print("Exiting the crypt. Farewell!")
                break
            elif command == "look":
                self.look_around()
            elif command == "inventory":
                self.show_inventory()
            elif command == "stats":
                self.show_stats()
            elif command.startswith("take ") or command.startswith("grab ") or command.startswith("pick up "):
                item = command.split(maxsplit=1)[1]
                if command.startswith("pick up"):
                    item = command.replace("pick up", "").strip()
                self.take_item(item)
            elif command.startswith("examine ") or command.startswith("inspect "):
                item = command.split(" ", 1)[1]
                self.examine_item(item)
            elif command.startswith("go "):
                direction = command.split(" ", 1)[1]
                self.move(direction)
            elif command == "attack":
                self.attack_enemy()
            elif command == "help":
                print("\n[Help Guide]")
                print(" - look: Re-read the current room description.")
                print(" - inventory: Check items you are carrying.")
                print(" - stats: View health, attack power, and location.")
                print(" - n, s, e, w: Quick shorthand for moving north, south, east, west.")
                print(" - take [item]: Pick up an item in the room.")
                print(" - examine [item]: Read detailed description of an item.")
                print(" - attack: Engage an enemy in combat.")
                print(" - quit: Exit the game.")
            else:
                print("Unknown command. Type 'help' for options.")

    def look_around(self):
        room = self.rooms[self.current_room]
        print(f"\n--- {room['title']} ---")
        print(room['desc'])
        
        if room['items']:
            for item in room['items']:
                item_name = self.items_db.get(item, {}).get('name', item)
                print(f"👉 You see a {item_name} here.")
        
        if room['enemy'] and room['enemy'] not in self.flags:
            enemy_name = self.enemies_db.get(room['enemy'], {}).get('name', room['enemy'])
            print(f"⚠️ A menacing {enemy_name} blocks your path!")

    def show_inventory(self):
        if not self.inventory:
            print("Your inventory is empty.")
        else:
            print("Inventory:")
            for item in self.inventory:
                name = self.items_db.get(item, {}).get('name', item)
                print(f" - {name}")

    def show_stats(self):
        print("\n--- CHARACTER STATUS ---")
        print(f"❤️ Health: {self.hp}/{self.player_stats.get('base_hp', 100)}")
        base_atk = self.player_stats.get('base_attack', 10)
        weapon_bonus = sum(self.items_db.get(item, {}).get('attack_bonus', 0) for item in self.inventory)
        print(f"⚔️ Attack Power: {base_atk + weapon_bonus} (Base: {base_atk} + Gear: {weapon_bonus})")
        print(f"🗺️ Current Location: {self.rooms[self.current_room]['title']}")

    def examine_item(self, item_name):
        room = self.rooms[self.current_room]
        found_item = None
        
        for item in self.inventory + room['items']:
            if item == item_name or self.items_db.get(item, {}).get('name', '').lower() == item_name:
                found_item = item
                break
        
        if found_item:
            item_data = self.items_db[found_item]
            print(f"🔍 {item_data.get('name', found_item)}: {item_data.get('description', 'An ordinary object.')}")
        else:
            print(f"You don't see any '{item_name}' here or in your inventory.")

    def take_item(self, item_name):
        room = self.rooms[self.current_room]
        matched_item = None
        for item in room['items']:
            if item == item_name or self.items_db.get(item, {}).get('name', '').lower() == item_name:
                matched_item = item
                break
        
        if matched_item:
            room['items'].remove(matched_item)
            self.inventory.append(matched_item)
            print(f"You picked up the {self.items_db[matched_item]['name']}.")
        else:
            print(f"There is no '{item_name}' here.")

    def move(self, direction):
        room = self.rooms[self.current_room]
        if direction in room['exits']:
            exit_info = room['exits'][direction]
            target = exit_info['target']
            req = exit_info['requires']

            if req:
                if req == 'rusted_key' and 'rusted_key' not in self.inventory:
                    print("🔒 The heavy wooden door is locked tight. You need a key!")
                    return
                elif req == 'skeleton_defeated' and 'skeleton_defeated' not in self.flags:
                    print("⚔️ The path is blocked! You must defeat the skeletal guardian first.")
                    return

            self.current_room = target
            
            if self.current_room == 'treasury':
                self.look_around()
                print("\n🏆 CONGRATULATIONS! You have claimed the Sunstone and escaped The Crypt of Echoes!")
                sys.exit(0)

            self.look_around()
        else:
            print("You cannot go that way.")

    def attack_enemy(self):
        room = self.rooms[self.current_room]
        enemy_id = room.get('enemy')
        
        if not enemy_id or enemy_id in self.flags:
            print("There is nothing to attack here.")
            return

        enemy = self.enemies_db[enemy_id]
        print(f"You engage the {enemy['name']} in combat!")
        
        has_sword = 'iron_sword' in self.inventory
        base_atk = self.player_stats.get('base_attack', 10)
        bonus = self.items_db.get('iron_sword', {}).get('attack_bonus', 0) if has_sword else 0
        total_player_dmg = max(1, (base_atk + bonus) - enemy.get('defense', 0))
        
        print(f"You strike with your weapon, dealing {total_player_dmg} damage!")
        
        if has_sword:
            print(enemy.get('defeat_text', 'You defeated the enemy!'))
            self.flags.add('skeleton_defeated')
            room['enemy'] = None
        else:
            print(f"Your bare fists bounce off the armor! The {enemy['name']} strikes back for {enemy.get('attack', 12)} damage.")
            self.hp -= enemy.get('attack', 12)
            print(f"Your HP: {self.hp}/100. Tip: You might need a weapon from the Armory!")
            if self.hp <= 0:
                print("You have fallen in battle... Game Over.")
                sys.exit(0)

if __name__ == "__main__":
    engine = GameEngine("game.ql")
    engine.start()