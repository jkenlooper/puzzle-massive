update NameRegister set approved = :name_approved, approved_date = datetime('now') where user = :player_id;
