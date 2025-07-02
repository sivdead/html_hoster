from flask import Flask
from html_hoster.database import db, Site, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///html_hoster/instance/db.sqlite'
db.init_app(app)

with app.app_context():
    sites_without_owner = Site.query.filter_by(user_id=None).all()
    print(f'找到 {len(sites_without_owner)} 个未关联用户的站点')
    
    # 如果有管理员用户，将所有未关联的站点关联到第一个管理员用户
    admin_user = User.query.filter_by(is_admin=True).first()
    if admin_user and sites_without_owner:
        print(f'将为这些站点设置用户ID: {admin_user.id} ({admin_user.username})')
        for site in sites_without_owner:
            site.user_id = admin_user.id
            print(f'站点 {site.name} ({site.id}) 现在关联到用户 {admin_user.username}')
        db.session.commit()
        print('更新完成!') 