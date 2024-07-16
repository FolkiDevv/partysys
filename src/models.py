from tortoise import fields, models


class Servers(models.Model):
    id = fields.IntField(primary_key=True)
    dis_id = fields.BigIntField()
    dis_adv_channel_id = fields.BigIntField()
    dis_wait_channel_id = fields.BigIntField()

    creator_channels: fields.ReverseRelation["CreatorChannels"]
    bans: fields.ReverseRelation["Bans"]

    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return self.dis_id


class CreatorChannels(models.Model):
    id = fields.IntField(primary_key=True)
    server: fields.ForeignKeyRelation[Servers] = fields.ForeignKeyField(
        'models.Servers',
        related_name='creator_channels'
    )
    dis_id = fields.BigIntField()
    dis_category_id = fields.BigIntField()
    def_name = fields.CharField(default="{user}", max_length=32)
    def_user_limit = fields.SmallIntField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.dis_id}'


class TempChannels(models.Model):
    id = fields.IntField(primary_key=True)
    dis_id = fields.BigIntField()
    dis_creator_id = fields.BigIntField()
    dis_owner_id = fields.BigIntField()
    dis_adv_msg_id = fields.BigIntField(null=True)
    deleted = fields.BooleanField(default=False)

    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.dis_id} by {self.dis_creator_id}'


class Bans(models.Model):
    id = fields.IntField(primary_key=True)
    server: fields.ForeignKeyRelation[Servers] = fields.ForeignKeyField(
        'models.Servers',
        related_name='bans'
    )
    dis_creator_id = fields.BigIntField()
    dis_banned_id = fields.BigIntField()
    banned = fields.BooleanField(default=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.dis_creator_id} banned user {self.dis_banned_id}'
