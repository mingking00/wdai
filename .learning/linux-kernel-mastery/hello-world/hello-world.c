/*
 * hello-world.c - 第一个内核模块
 * 验证技巧1-3:
 *   1. module_init/exit() 宏
 *   2. __init/__exit 内存优化
 *   3. 版本兼容性处理
 */

#include <linux/init.h>      /* __init, __exit */
#include <linux/module.h>    /* module_init/exit */
#include <linux/printk.h>    /* pr_info */
#include <linux/version.h>   /* LINUX_VERSION_CODE */

/* 模块参数示例 - 技巧扩展 */
static char *name = "world";
module_param(name, charp, S_IRUGO);
MODULE_PARM_DESC(name, "The name to display in greeting");

/* 
 * __init 标记: 模块加载后此函数内存可释放
 * 技巧2应用: 内存优化
 */
static int __init hello_init(void)
{
    pr_info("Hello, %s!\n", name);
    pr_info("Kernel version: %d.%d.%d\n", 
            LINUX_VERSION_CODE >> 16,
            (LINUX_VERSION_CODE >> 8) & 0xFF,
            LINUX_VERSION_CODE & 0xFF);
    return 0;
}

/*
 * __exit 标记: 内置驱动时省略此函数
 * 技巧2应用: 内存优化
 */
static void __exit hello_exit(void)
{
    pr_info("Goodbye, %s!\n", name);
}

/* 
 * 技巧1应用: 使用module_init/exit宏
 * 比旧式init_module()/cleanup_module()更清晰
 */
module_init(hello_init);
module_exit(hello_exit);

/* 模块信息 */
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Kimi Claw");
MODULE_DESCRIPTION("Hello World kernel module for learning");
MODULE_VERSION("1.0");
