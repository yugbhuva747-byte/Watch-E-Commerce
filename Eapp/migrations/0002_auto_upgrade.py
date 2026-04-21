from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Eapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(model_name='user', name='phone', field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(model_name='user', name='address', field=models.TextField(blank=True)),
        migrations.AddField(model_name='watch', name='category', field=models.CharField(choices=[('classic','Classic'),('sport','Sport'),('limited','Limited Edition'),('new','New Arrival')], default='classic', max_length=20)),
        migrations.AddField(model_name='watch', name='material', field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='watch', name='movement', field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='watch', name='is_featured', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='watch', name='is_active', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='watch', name='views_count', field=models.IntegerField(default=0)),
        migrations.AddField(model_name='cart', name='added_at', field=models.DateTimeField(auto_now_add=True, null=True)),
        migrations.AddField(model_name='order', name='status', field=models.CharField(choices=[('pending','Pending'),('confirmed','Confirmed'),('shipped','Shipped'),('delivered','Delivered'),('cancelled','Cancelled')], default='pending', max_length=20)),
        migrations.AddField(model_name='order', name='shipping_address', field=models.TextField(blank=True)),
        migrations.AddField(model_name='orderitem', name='price', field=models.FloatField(default=0)),
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField()),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('subject', models.CharField(blank=True, max_length=200)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('rating', models.IntegerField(default=5)),
                ('comment', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('watch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='Eapp.watch')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Eapp.user')),
            ],
        ),
    ]
