import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Getstarted } from './getstarted';

describe('Getstarted', () => {
  let component: Getstarted;
  let fixture: ComponentFixture<Getstarted>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Getstarted]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Getstarted);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
