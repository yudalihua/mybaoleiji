from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser,PermissionsMixin
)

# Create your models here.


#主机列表
class Host(models.Model):
    #主机名、ip地址都不能重复
    name = models.CharField(max_length=64,unique=True)
    ip_addr = models.GenericIPAddressField(unique=True)
    port = models.SmallIntegerField(default=22)
    idc = models.ForeignKey("IDC",on_delete=models.CASCADE)
    #remote_users = models.ManyToManyField("RemoteUser")

    def __str__(self):
        return self.name

#存储主机组，把一组机器归为某个组，然后分给某个人
class HostGroup(models.Model):
    name = models.CharField(max_length=64,unique=True)
    #hosts = models.ManyToManyField("Host")
    host_to_remote_users = models.ManyToManyField("HostToRemoteUser")

    def __str__(self):
        return self.name

#主机和远程用户的关系
class HostToRemoteUser(models.Model):
    host = models.ForeignKey("Host",on_delete=models.CASCADE)
    remote_user = models.ForeignKey("RemoteUser",on_delete=models.CASCADE)

    class Meta:
        unique_together = ("host","remote_user")


    def __str__(self):
        return "%s %s"%(self.host,self.remote_user)

# 堡垒机上管理的远程主机的账号信息
class RemoteUser(models.Model):
    auth_type_choices = ((0,'ssh-password'),(1,'ssh-key'))
    auth_type = models.SmallIntegerField(choices=auth_type_choices,default=0)
    username = models.CharField(max_length=32)
    #如果用ssh的key登录的话就不需要密码，所以password可以为空。
    password = models.CharField(max_length=64,blank=True,null=True)

    class Meta:
        unique_together = ('auth_type','username','password')

    #在admin中，输出这个类的对象的时候，以下边的形式。
    def __str__(self):
        return "%s : %s" %(self.username,self.password)

class UserProfileManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            name=name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
            name=name,
        )
        user.is_superuser = True
        user.save(using=self._db)
        return user

#登录堡垒机的账号，不同的堡垒机账号能够登录不同的机器。
class UserProfile(AbstractBaseUser,PermissionsMixin):
    email = models.EmailField(verbose_name='email address',max_length=255,unique=True,)
    name = models.CharField(max_length=64, verbose_name="姓名")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    objects = UserProfileManager()

    #未分组的机器直接和用户关联。
    host_to_remote_users = models.ManyToManyField("HostToRemoteUser",blank=True,null=True)
    host_groups = models.ManyToManyField("HostGroup",blank=True)

    #登录admin使用的用户名字段是这张表的email字段
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):              # __unicode__ on Python 2
        return self.email





#存储机房信息
class IDC(models.Model):
    name = models.CharField(max_length=64,unique=True)
    def __str__(self):
        return self.name

#存储用户通过堡垒机操作远程主机的日志。
class AuditLog(models.Model):
    user = models.ForeignKey("UserProfile",verbose_name="堡垒机账号",null=True,blank=True,on_delete=models.CASCADE)
    host_to_remote_user = models.ForeignKey("HostToRemoteUser" ,null=True,blank=True,on_delete=models.CASCADE)
    log_type_choices = ((0,'login'),(1,'cmd'),(2,'logout'))
    log_type = models.SmallIntegerField(choices=log_type_choices,default=0)
    content = models.CharField(max_length=255,null=True,blank=True)
    date = models.DateTimeField(auto_now_add=True,null=True,blank=True)

    def __str__(self):
        return "%s %s" %(self.host_to_remote_user, self.content)





class Task(models.Model):
    """批量任务"""
    task_type_choices = (('cmd','批量命令'),('file-transfer','文件传输'))
    task_type = models.CharField(choices=task_type_choices,max_length=64)
    content = models.CharField(max_length=255, verbose_name="任务内容")
    user = models.ForeignKey("UserProfile",on_delete=models.CASCADE)

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s %s"%(self.task_type,self.content)



class TaskLogDetail(models.Model):
    """存储大任务子结果"""
    task = models.ForeignKey("Task",on_delete=models.CASCADE)
    host_to_remote_user = models.ForeignKey("HostToRemoteUser",on_delete=models.CASCADE)
    result = models.TextField(verbose_name="任务执行结果")

    status_choices = ((0,'initialized'),(1,'sucess'),(2,'failed'),(3,'timeout'))
    status = models.SmallIntegerField(choices=status_choices,default=0)

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s %s"%(self.task,self.host_to_remote_user)