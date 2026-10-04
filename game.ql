# The Crypt of Echoes - Game Script

player {
    start_room entrance
    base_hp 100
    base_attack 10
}

item rusted_key {
    name "Rusted Key"
    description "An old iron key covered in orange rust, smelling of damp earth."
    type "key"
}

item iron_sword {
    name "Iron Sword"
    description "A sturdy, well-balanced blade left behind by a fallen adventurer."
    type "weapon"
    attack_bonus 15
}

room entrance {
    title "The Damp Entrance"
    desc "Water drips from the cracked stone ceiling, echoing in the dark. A heavy wooden door lies to the north, but it is locked."
    item rusted_key
    go north -> guardian_hall [requires rusted_key]
    go east -> armory
}

room armory {
    title "The Armory"
    desc "Racks of broken weapons line the walls. A flickering torch illuminates a dusty workbench."
    item iron_sword
    go west -> entrance
}

enemy skeleton {
    name "Skeletal Guardian"
    hp 40
    attack 12
    defense 5
    defeat_text "You strike a decisive blow, shattering the skeleton's bones into dust!"
}

room guardian_hall {
    title "The Guardian's Chamber"
    desc "A massive, vaulted stone hall. A skeletal guardian blocks the exit ahead, its eyes glowing with pale blue fire."
    enemy skeleton
    go south -> entrance
    go north -> treasury [requires skeleton_defeated]
}

room treasury {
    title "The Treasury"
    desc "Piles of forgotten gold coins and the glowing Sunstone artifact rest on a high stone altar. You have won!"
}