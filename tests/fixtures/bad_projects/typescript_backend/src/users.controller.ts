export class UsersController {
    private repository: any;

    getUsers(): any {
        // NEST-002: Direct database / ORM access inside controller
        return this.repository.find();
    }
}

