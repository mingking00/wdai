/*
 * chardev.c - 字符设备驱动验证
 * 验证技巧4-6:
 *   4. cdev接口 (vs 旧register_chrdev)
 *   5. atomic_cmpxchg无锁并发
 *   6. copy_to/from_user安全拷贝
 * 
 * 验证步骤:
 *   1. make
 *   2. sudo insmod chardev.ko
 *   3. sudo mknod /dev/mychardev c $(cat /proc/devices | grep mychardev | awk '{print $1}') 0
 *   4. echo "test" | sudo tee /dev/mychardev
 *   5. cat /dev/mychardev
 *   6. sudo rmmod chardev
 */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/cdev.h>      // cdev接口
#include <linux/fs.h>
#include <linux/device.h>
#include <linux/uaccess.h>   // copy_to/from_user
#include <linux/atomic.h>    // atomic操作
#include <linux/slab.h>

#define DEVICE_NAME "mychardev"
#define CLASS_NAME "mychar"
#define BUFFER_SIZE 1024

static int major;
static struct class *my_class = NULL;
static struct device *my_device = NULL;
static struct cdev my_cdev;  // 技巧4: 使用cdev而非register_chrdev

// 设备数据
struct my_device_data {
    char buffer[BUFFER_SIZE];
    atomic_t is_open;  // 技巧5: atomic_cmpxchg防并发
    size_t data_len;
};

static struct my_device_data *device_data = NULL;

// 打开设备
static int my_open(struct inode *inode, struct file *file)
{
    // 技巧5: 使用atomic_cmpxchg实现无锁并发控制
    if (atomic_cmpxchg(&device_data->is_open, 0, 1) != 0) {
        pr_info("Device already open, rejecting\n");
        return -EBUSY;
    }
    
    pr_info("Device opened\n");
    return 0;
}

// 关闭设备
static int my_release(struct inode *inode, struct file *file)
{
    atomic_set(&device_data->is_open, 0);
    pr_info("Device closed\n");
    return 0;
}

// 读取设备
static ssize_t my_read(struct file *file, char __user *user_buffer, 
                       size_t len, loff_t *offset)
{
    size_t to_copy;
    ssize_t copied;
    
    if (*offset >= device_data->data_len)
        return 0;  // EOF
    
    to_copy = min(len, (size_t)(device_data->data_len - *offset));
    
    // 技巧6: 使用copy_to_user安全拷贝到用户空间
    if (copy_to_user(user_buffer, device_data->buffer + *offset, to_copy)) {
        pr_err("copy_to_user failed\n");
        return -EFAULT;
    }
    
    *offset += to_copy;
    copied = to_copy;
    
    pr_info("Read %zu bytes\n", copied);
    return copied;
}

// 写入设备
static ssize_t my_write(struct file *file, const char __user *user_buffer,
                        size_t len, loff_t *offset)
{
    size_t to_copy;
    
    if (*offset >= BUFFER_SIZE - 1)
        return -ENOSPC;  // 缓冲区满
    
    to_copy = min(len, (size_t)(BUFFER_SIZE - 1 - *offset));
    
    // 技巧6: 使用copy_from_user安全拷贝从用户空间
    if (copy_from_user(device_data->buffer + *offset, user_buffer, to_copy)) {
        pr_err("copy_from_user failed\n");
        return -EFAULT;
    }
    
    device_data->data_len = *offset + to_copy;
    device_data->buffer[device_data->data_len] = '\0';
    *offset += to_copy;
    
    pr_info("Written %zu bytes: %s\n", to_copy, device_data->buffer);
    return to_copy;
}

// 文件操作表
static struct file_operations fops = {
    .owner = THIS_MODULE,
    .open = my_open,
    .release = my_release,
    .read = my_read,
    .write = my_write,
};

// 初始化模块
static int __init my_init(void)
{
    dev_t dev;
    int ret;
    
    pr_info("Loading chardev module...\n");
    
    // 分配设备数据
    device_data = kzalloc(sizeof(*device_data), GFP_KERNEL);
    if (!device_data)
        return -ENOMEM;
    
    atomic_set(&device_data->is_open, 0);
    device_data->data_len = 0;
    strcpy(device_data->buffer, "Hello from kernel!\n");
    device_data->data_len = strlen(device_data->buffer);
    
    // 技巧4: 使用新的cdev接口
    // 1. 分配设备号
    ret = alloc_chrdev_region(&dev, 0, 1, DEVICE_NAME);
    if (ret < 0) {
        pr_err("Failed to allocate device number\n");
        kfree(device_data);
        return ret;
    }
    major = MAJOR(dev);
    pr_info("Allocated major number: %d\n", major);
    
    // 2. 创建类
    my_class = class_create(CLASS_NAME);
    if (IS_ERR(my_class)) {
        pr_err("Failed to create class\n");
        unregister_chrdev_region(dev, 1);
        kfree(device_data);
        return PTR_ERR(my_class);
    }
    
    // 3. 初始化cdev
    cdev_init(&my_cdev, &fops);
    my_cdev.owner = THIS_MODULE;
    
    // 4. 添加cdev到系统
    ret = cdev_add(&my_cdev, dev, 1);
    if (ret) {
        pr_err("Failed to add cdev\n");
        class_destroy(my_class);
        unregister_chrdev_region(dev, 1);
        kfree(device_data);
        return ret;
    }
    
    // 5. 创建设备文件
    my_device = device_create(my_class, NULL, dev, NULL, DEVICE_NAME);
    if (IS_ERR(my_device)) {
        pr_err("Failed to create device\n");
        cdev_del(&my_cdev);
        class_destroy(my_class);
        unregister_chrdev_region(dev, 1);
        kfree(device_data);
        return PTR_ERR(my_device);
    }
    
    pr_info("Chardev loaded successfully\n");
    return 0;
}

// 清理模块
static void __exit my_exit(void)
{
    dev_t dev = MKDEV(major, 0);
    
    pr_info("Unloading chardev module...\n");
    
    device_destroy(my_class, dev);
    cdev_del(&my_cdev);
    class_destroy(my_class);
    unregister_chrdev_region(dev, 1);
    kfree(device_data);
    
    pr_info("Chardev unloaded\n");
}

module_init(my_init);
module_exit(my_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Kimi Claw");
MODULE_DESCRIPTION("Character device driver for verification");
